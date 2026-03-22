"""
Sequential Combination MCP Server
FastMCP server exposing 6 tools for semantic skill search and expertise injection.
Designed for the antigravity-awesome-skills repository (1200+ skills).
"""

import os
import re
import json
import logging
import asyncio
from pathlib import Path
from typing import List, Optional, Dict, Any

from fastmcp import FastMCP
from sentence_transformers import SentenceTransformer
from skills_index import SkillsIndexer

# ─────────────────────────────────────────────
# SETUP
# ─────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("sequential-combination")

BASE_DIR = Path(__file__).parent.parent.absolute()
COMBOS_SEED_PATH = BASE_DIR / "config" / "combos_seed.json"

# Initialize MCP
mcp = FastMCP("sequential-combination")

# Global state
_indexer: Optional[SkillsIndexer] = None
_indexer_lock = asyncio.Lock()


def get_model():
    """Load the SentenceTransformer model (synchronous)."""
    logger.info("Loading SentenceTransformer model...")
    return SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")


async def get_indexer() -> SkillsIndexer:
    """Lazy-initialization of the SkillsIndexer with thread-safe lock."""
    global _indexer
    async with _indexer_lock:
        if _indexer is None:
            logger.info("Initializing SkillsIndexer...")
            _indexer = SkillsIndexer(str(BASE_DIR))
            loop = asyncio.get_event_loop()
            model = await loop.run_in_executor(None, get_model)
            _indexer.set_model(model)
            logger.info("SkillsIndexer ready.")
    return _indexer


def load_expert_combos() -> Dict[str, List[str]]:
    """Load and flatten predefined expert combinations from combos_seed.json."""
    if COMBOS_SEED_PATH.exists():
        try:
            with open(COMBOS_SEED_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
                combos_list = data.get("combos", [])
                return {c["name"]: c["skills"] for c in combos_list if "name" in c and "skills" in c}
        except Exception as e:
            logger.error(f"Error loading expert combos: {e}")
    return {}


# ─────────────────────────────────────────────
# TOOL 1: list_stages
# ─────────────────────────────────────────────

@mcp.tool()
async def list_stages() -> List[str]:
    """List all available cognitive stages defined in stage_profiles.yaml."""
    indexer = await get_indexer()
    profiles = indexer.get_profiles()
    return list(profiles.keys())


# ─────────────────────────────────────────────
# TOOL 2: suggest_combo
# ─────────────────────────────────────────────

@mcp.tool()
async def suggest_combo(task: str, stage: str, n: int = 5) -> Dict[str, Any]:
    """
    Search and suggest the best skill combinations for a task and cognitive stage.

    Args:
        task: The task description to find relevant skills for.
        stage: The cognitive stage (e.g., 'analysis', 'implementation').
        n: Number of skills to suggest (default: 5).
    """
    indexer = await get_indexer()

    # 1. Check for Expert Combos (Seed)
    expert_combos = load_expert_combos()
    expert_match = None
    for key, skills in expert_combos.items():
        if re.search(rf"\b{re.escape(key)}\b", task, re.IGNORECASE):
            expert_match = {"name": key, "skills": skills}
            break

    # 2. Semantic search
    suggested_skills = indexer.query_skills(task, stage, n_results=n)

    msg = f"Suggestions for '{task}' at stage '{stage}':"
    if expert_match and isinstance(expert_match, dict):
        expert_name = expert_match.get("name", "Expert")
        msg = f"Expert Match Found: '{expert_name}'. " + msg

    return {
        "message": msg,
        "expert_combo": expert_match,
        "skills": suggested_skills
    }


# ─────────────────────────────────────────────
# TOOL 3: get_expert_dna
# ─────────────────────────────────────────────

@mcp.tool()
async def get_expert_dna(skills: List[str]) -> str:
    """
    Get the 'Expert DNA' (condensed expertise) for a list of skills.
    This is much more token-efficient than load_combo_content.

    Args:
        skills: List of skill IDs to extract DNA from.
    """
    indexer = await get_indexer()
    return indexer.load_dna_content(skills)


# ─────────────────────────────────────────────
# TOOL 4: load_combo_content
# ─────────────────────────────────────────────

@mcp.tool()
async def load_combo_content(skills: List[str]) -> str:
    """
    Load the combined content (SKILL.md) for a list of skills.
    More comprehensive than DNA — includes methodology, examples, usage sections.

    Args:
        skills: List of skill IDs to load.
    """
    indexer = await get_indexer()
    return indexer.load_combination_content(skills)


# ─────────────────────────────────────────────
# TOOL 5: suggest_and_inject (NEW)
# ─────────────────────────────────────────────

@mcp.tool()
async def suggest_and_inject(task: str, stage: str, mode: str = "dna", n: int = 5) -> Dict[str, Any]:
    """
    Combined tool: finds the best skills AND injects their expertise in one call.
    Use this for quick workflows. For advanced workflows (double-pass protocol),
    prefer suggest_combo + sequential-thinking validation + get_expert_dna separately.

    Args:
        task: The task description.
        stage: The cognitive stage (e.g., 'analysis', 'synthesis').
        mode: Injection mode — 'dna' (surgical, default) or 'full' (comprehensive).
        n: Number of skills to suggest and inject (default: 5).
    """
    indexer = await get_indexer()

    # 1. Suggest
    suggested = indexer.query_skills(task, stage, n_results=n)
    skill_ids = [s["id"] for s in suggested]

    # 2. Inject based on mode
    if mode == "full":
        content = indexer.load_combination_content(skill_ids)
    else:
        content = indexer.load_dna_content(skill_ids)

    # 3. Check for expert combo bonus
    expert_combos = load_expert_combos()
    expert_match = None
    for key, combo_skills in expert_combos.items():
        if re.search(rf"\b{re.escape(key)}\b", task, re.IGNORECASE):
            expert_match = {"name": key, "skills": combo_skills}
            break

    return {
        "message": f"Injected {len(skill_ids)} experts ({mode} mode) for stage '{stage}'",
        "expert_combo": expert_match,
        "skills_used": suggested,
        "injected_content": content
    }


# ─────────────────────────────────────────────
# TOOL 6: ping
# ─────────────────────────────────────────────

@mcp.tool()
async def ping() -> str:
    """Simple health check to verify the server is responding."""
    return "pong"


# ─────────────────────────────────────────────
# ENTRY POINT
# ─────────────────────────────────────────────

if __name__ == "__main__":
    # Ensure data directories exist
    (BASE_DIR / "data" / "chroma_db").mkdir(parents=True, exist_ok=True)

    logger.info("Starting Sequential Combination MCP Server...")
    mcp.run()
