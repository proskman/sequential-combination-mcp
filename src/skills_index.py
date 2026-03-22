"""
Sequential Combination — Skills Indexer
Moteur de recherche sémantique + extraction DNA pour les skills antigravity-awesome-skills.
Utilise SentenceTransformer (paraphrase-multilingual-MiniLM-L12-v2) + ChromaDB.
"""

import re
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

import yaml
import chromadb
from sentence_transformers import SentenceTransformer

logger = logging.getLogger("sequential-combination.indexer")


class SkillsIndexer:
    """
    Indexe les SKILL.md du répertoire antigravity-awesome-skills dans ChromaDB
    et fournit la recherche sémantique + extraction DNA.
    """

    def __init__(self, base_dir: str):
        self.base_dir = Path(base_dir)
        self.skills_dir = self.base_dir / "skills"
        self.profiles_path = self.base_dir / "config" / "stage_profiles.yaml"
        # ChromaDB setup
        chroma_path = self.base_dir / "data" / "chroma_db"
        self.client = chromadb.PersistentClient(path=str(chroma_path))
        self.collection = self.client.get_or_create_collection(
            name="skills_v2",
            metadata={"hnsw:space": "cosine"}
        )
        self.model: Optional[SentenceTransformer] = None

    def set_model(self, model: SentenceTransformer):
        """Set the embedding model after initialization."""
        self.model = model

    def get_profiles(self) -> Dict[str, List[str]]:
        """Load cognitive stage profiles from YAML config."""
        if self.profiles_path.exists():
            with open(self.profiles_path, "r", encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
        logger.warning(f"Stage profiles not found at {self.profiles_path}")
        return {}

    # ─────────────────────────────────────────────
    # INDEX — Scans skills/ and builds ChromaDB embeddings
    # ─────────────────────────────────────────────

    def refresh_index(self):
        """Rebuild the ChromaDB index from all SKILL.md files in skills/."""
        if not self.model:
            raise RuntimeError("Embedding model not set. Call set_model() first.")

        if not self.skills_dir.exists():
            logger.error(f"Skills directory not found: {self.skills_dir}")
            return

        logger.info(f"Refreshing index from {self.skills_dir}...")
        all_ids, all_documents, all_metadatas = [], [], []
        batch_size = 100

        for skill_dir in sorted(self.skills_dir.iterdir()):
            if not skill_dir.is_dir():
                continue

            skill_files = list(skill_dir.rglob("SKILL.md"))
            if not skill_files:
                continue

            try:
                with open(skill_files[0], "r", encoding="utf-8") as f:
                    content = f.read()

                skill_id = skill_dir.name
                all_ids.append(skill_id)
                all_documents.append(content[:2000])  # Truncate for embedding
                all_metadatas.append({"name": skill_id, "path": str(skill_files[0])})

                # Batch insert
                if len(all_ids) >= batch_size:
                    embeddings = self.model.encode(all_documents).tolist()
                    self.collection.upsert(
                        ids=all_ids,
                        embeddings=embeddings,
                        documents=all_documents,
                        metadatas=all_metadatas
                    )
                    logger.info(f"Indexed {len(all_ids)} skills...")
                    all_ids, all_documents, all_metadatas = [], [], []

            except Exception as e:
                logger.error(f"Error indexing {skill_dir.name}: {e}")

        # Final batch
        if all_ids:
            embeddings = self.model.encode(all_documents).tolist()
            self.collection.upsert(
                ids=all_ids,
                embeddings=embeddings,
                documents=all_documents,
                metadatas=all_metadatas
            )
        logger.info(f"Index refresh complete. Total skills in collection: {self.collection.count()}")

    # ─────────────────────────────────────────────
    # QUERY — Semantic search with stage keyword boost
    # ─────────────────────────────────────────────

    def query_skills(self, query: str, stage: str, n_results: int = 5) -> List[Dict[str, Any]]:
        """
        Search skills by semantic similarity, boosted by stage keyword matching.
        Returns top n_results sorted by combined score.
        """
        if not self.model:
            logger.error("Embedding model not initialized.")
            return []

        # Stage keyword boost
        profiles = self.get_profiles()
        keywords = profiles.get(stage, [])

        # Semantic search — over-fetch for manual filtering
        query_embedding = self.model.encode(query).tolist()
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=min(n_results * 3, 50),
            include=["metadatas", "distances", "documents"]
        )

        filtered = []
        for i in range(len(results["ids"][0])):
            skill_id = results["ids"][0][i]
            metadata = results["metadatas"][0][i]
            document = results["documents"][0][i]
            distance = results["distances"][0][i]

            # Combined score: semantic distance - stage keyword boost
            # Lower distance = more similar. Boost reduces distance for stage-relevant skills.
            keyword_hits = sum(1 for kw in keywords if kw.lower() in document.lower())
            boost = keyword_hits * 0.05
            adjusted_score = float(distance) - boost  # Lower = better

            filtered.append({
                "id": skill_id,
                "name": metadata.get("name", skill_id),
                "score": adjusted_score,
                "keyword_boost": keyword_hits,
                "description": document[:300]
            })

        # Sort by adjusted score (ascending = better match)
        filtered.sort(key=lambda x: x["score"])
        return filtered[:n_results]

    # ─────────────────────────────────────────────
    # DNA — Surgical extraction of core rules from SKILL.md
    # ─────────────────────────────────────────────

    def extract_expert_dna(self, content: str, skill_id: str) -> str:
        """
        Extract condensed 'Expert DNA' from a SKILL.md file.
        Targets sections: Instructions, Rules, Methodology, Directives,
        Core, Principles, Best Practices, When to Use.
        Falls back to extracting bullet points if no named section found.

        Returns a compact string with only the actionable rules.
        """
        target_keywords = [
            'instructions', 'core instructions',
            'rules', 'core rules', 'directives',
            'methodology', 'core', 'how-to', 'principles',
            'best practices', 'when to use'
        ]

        dna_sections = []

        # Strategy 1: Find named sections (## heading matching target keywords)
        section_pattern = r'^#{1,3}\s+(.+?)$'
        sections = re.split(section_pattern, content, flags=re.MULTILINE)

        for i in range(1, len(sections), 2):
            heading = sections[i].strip().lower()
            body = sections[i + 1] if i + 1 < len(sections) else ""

            if any(kw in heading for kw in target_keywords):
                # Extract bullet points and numbered lists from this section
                lines = body.strip().split('\n')
                important_lines = [
                    line.strip() for line in lines
                    if line.strip().startswith(('-', '*', '•', '+'))
                    or re.match(r'^\d+\.', line.strip())
                ]
                if important_lines:
                    section_content = '\n'.join(important_lines[:20])  # Cap per section
                    dna_sections.append(f"### {sections[i].strip()}\n{section_content}")

        # Strategy 2: Fallback — extract ALL bullet points from content
        if not dna_sections:
            logger.info(f"No named DNA sections found for '{skill_id}', using bullet fallback.")
            all_bullets = re.findall(r'^[\s]*[-*•+]\s+.+$', content, re.MULTILINE)
            if all_bullets:
                dna_sections.append(
                    f"### Core Rules (Direct Extraction)\n" +
                    '\n'.join(b.strip() for b in all_bullets[:15])
                )

        if not dna_sections:
            logger.warning(f"No DNA extractable for '{skill_id}'. Returning first lines.")
            lines = content.strip().split('\n')
            return '\n'.join(lines[:5])

        return '\n'.join(dna_sections)

    # ─────────────────────────────────────────────
    # LOAD — Read full skill content or DNA from files
    # ─────────────────────────────────────────────

    def _find_skill_file(self, skill_id: str) -> Optional[Path]:
        """Find the SKILL.md file for a given skill ID."""
        skill_path = self.skills_dir / skill_id
        if skill_path.is_dir():
            files = list(skill_path.rglob("SKILL.md"))
            if files:
                return files[0]
        # Fallback: check ChromaDB metadata
        try:
            result = self.collection.get(ids=[skill_id], include=["metadatas"])
            if result and result["metadatas"]:
                path_str = result["metadatas"][0].get("path")
                if path_str:
                    found = Path(path_str)
                    if found.exists():
                        return found
        except Exception:
            pass
        logger.warning(f"Skill file not found for '{skill_id}'")
        return None

    def load_dna_content(self, skill_ids: List[str]) -> str:
        """
        Load extracted Expert DNA for multiple skills.
        Token-efficient: returns only core rules and methodology.
        """
        parts = []
        for sid in skill_ids:
            file_path = self._find_skill_file(sid)
            if not file_path:
                parts.append(f"## EXPERT DNA: {sid}\n*Skill file not found.*")
                continue
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                dna = self.extract_expert_dna(content, sid)
                parts.append(f"## EXPERT DNA: {sid}\n{dna}")
            except Exception as e:
                logger.error(f"Error extracting DNA for {sid}: {e}")
                parts.append(f"## EXPERT DNA: {sid}\n*Error: {e}*")

        return "\n\n---\n\n".join(parts)

    def load_combination_content(self, skill_ids: List[str]) -> str:
        """
        Load combined content from SKILL.md files — targeted sections only.
        More comprehensive than DNA but still selective.
        Extracts: Methodology, Instructions, Rules, Examples.
        """
        target_sections = [
            'methodology', 'instructions', 'rules', 'directives',
            'core', 'examples', 'usage', 'implementation'
        ]

        parts = []
        for sid in skill_ids:
            file_path = self._find_skill_file(sid)
            if not file_path:
                parts.append(f"## SKILL CONTENT: {sid}\n*Skill file not found.*")
                continue
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()

                # Extract targeted sections
                extracted = self._extract_sections(content, target_sections)
                if extracted:
                    parts.append(f"## SKILL CONTENT: {sid}\n{extracted}")
                else:
                    # Fallback: return first 3000 chars
                    parts.append(f"## SKILL CONTENT: {sid}\n{content[:3000]}")
            except Exception as e:
                logger.error(f"Error loading content for {sid}: {e}")
                parts.append(f"## SKILL CONTENT: {sid}\n*Error: {e}*")

        return "\n\n---\n\n".join(parts)

    def _extract_sections(self, content: str, target_keywords: List[str]) -> str:
        """Extract named sections from markdown content matching target keywords."""
        section_pattern = r'^#{1,3}\s+(.+?)$'
        sections = re.split(section_pattern, content, flags=re.MULTILINE)
        extracted = []

        for i in range(1, len(sections), 2):
            heading = sections[i].strip().lower()
            body = sections[i + 1] if i + 1 < len(sections) else ""

            if any(kw in heading for kw in target_keywords):
                trimmed = body.strip()[:2000]  # Cap per section
                extracted.append(f"### {sections[i].strip()}\n{trimmed}")

        return '\n\n'.join(extracted)
