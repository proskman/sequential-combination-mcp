# 🧬 EXPLANATION — Internal Workflow of the Sequential Combination MCP

This document describes in detail how each component of the MCP works,
with flow diagrams to visualize the internal mechanisms.

---

## 1. Overview

Sequential Combination is an **MCP server** (Model Context Protocol) that acts as a
**smart librarian** for expertise skills. It:

1. **Indexes** all `SKILL.md` files in a vector database (ChromaDB)
2. **Searches** the most relevant skills for a given task via semantic similarity
3. **Injects** the extracted expertise (DNA or full content) into the LLM's context

The goal: **the LLM does not use its internal memory** for methodologies; it uses
structured expertise from SKILL.md files, verified and maintained by the community.

---

## 2. Global Architecture

```mermaid
graph TB
    subgraph "MCP Server (stdio)"
        A["server.py<br/>FastMCP — 6 tools"]
        B["skills_index.py<br/>SkillsIndexer"]
    end

    subgraph "Storage"
        C["ChromaDB<br/>Vector database"]
        D["skills/<br/>antigravity-awesome-skills<br/>1200+ SKILL.md"]
        E["config/<br/>stage_profiles.yaml<br/>combos_seed.json"]
    end

    subgraph "ML Model"
        F["SentenceTransformer<br/>paraphrase-multilingual-MiniLM-L12-v2"]
    end

    A -->|"uses"| B
    B -->|"stores/searches vectors"| C
    B -->|"reads files"| D
    B -->|"loads config"| E
    B -->|"encodes text → vector"| F
```

---

## 3. The 6 Tools — Details

### 3.1 `list_stages`
**Role**: Returns the list of available cognitive stages.
**Source**: `config/stage_profiles.yaml`
**Flow**: YAML read → key extraction → JSON return

### 3.2 `suggest_combo(task, stage, n=5)`
**Role**: Finds the N best skills for a task at a given cognitive stage.
**Detailed flow**: see diagram below (Section 4).

### 3.3 `get_expert_dna(skills)`
**Role**: Surgical extraction of a skill's rules/methodologies.
**Token-efficient**: returns ~15-30 bullets instead of 200+ lines.
**Detailed flow**: see diagram below (Section 5).

### 3.4 `load_combo_content(skills)`
**Role**: Loads targeted sections of the SKILL.md (more comprehensive than DNA).
**Target sections**: Instructions, Methodology, Implementation, Workflow, Architecture.

### 3.5 `suggest_and_inject(task, stage, mode, n)`
**Role**: Combined — performs `suggest_combo` + DNA/full injection in a single call.
**Usage**: Simple workflows where intermediate ST validation is not necessary.

### 3.6 `ping`
**Role**: Health check. Returns "pong".

---

## 4. `suggest_combo` Flow — Semantic Search

```mermaid
sequenceDiagram
    participant LLM as LLM (Client)
    participant SRV as server.py
    participant IDX as SkillsIndexer
    participant ST as SentenceTransformer
    participant CDB as ChromaDB
    participant CFG as stage_profiles.yaml
    participant SEED as combos_seed.json

    LLM->>SRV: suggest_combo("secure API", "Analysis", n=5)
    SRV->>IDX: query_skills("secure API", "Analysis", 5)

    Note over IDX: Step 1 — Embeddings
    IDX->>ST: encode("secure API")
    ST-->>IDX: vector [0.12, -0.34, ...]

    Note over IDX: Step 2 — Vector search
    IDX->>CDB: query(embedding, n=15)
    CDB-->>IDX: 15 skills + distances

    Note over IDX: Step 3 — Keyword Boost
    IDX->>CFG: profiles["Analysis"]
    CFG-->>IDX: ["compare","evaluate","benchmark","security","architecture",...]

    Note over IDX: For each skill:<br/>adjusted_score = distance - (keyword_hits × 0.05)

    Note over IDX: Step 4 — Sort by adjusted_score (ascending)

    IDX-->>SRV: Top 5 sorted skills

    Note over SRV: Step 5 — Combo Seeds
    SRV->>SEED: regex match "secure API"
    SEED-->>SRV: match? → expert_combo bonus

    SRV-->>LLM: {skills: [...], expert_combo: ...}
```

### How sorting works

ChromaDB returns **cosine distances** (0 = identical, 2 = opposite).
Stage profiling **reduces** this distance for skills containing stage keywords:

```
Raw score    = cosine distance (e.g., 0.85)
Keyword hits = number of stage keywords found in SKILL.md (e.g., 3)
Boost        = hits × 0.05 (e.g., 0.15)
Final score  = 0.85 - 0.15 = 0.70 ← this skill moves up in the ranking
```

Without stage keywords: the score remains raw.
With 3 matching keywords: the skill gets a 0.15 point boost.

---

## 5. DNA Engine — Expertise Extraction

DNA (Expert DNA) is the **surgical** extraction of rules and methodologies
from a SKILL.md, without all the superfluous content.

```mermaid
flowchart TD
    A["get_expert_dna(skill_id)"] --> B{"Find SKILL.md<br/>in skills/skill_id/"}
    B -->|"Found"| C["Read file content"]
    B -->|"Not found"| Z["Search in ChromaDB metadata"]

    C --> D["Split by ## headings"]
    D --> E{"Recognized section?<br/>Rules, Instructions, Methodology,<br/>Best Practices, When to Use, etc."}

    E -->|"YES"| F["Extract bullets<br/>(-, *, •, 1., 2.)<br/>max 20 per section"]
    E -->|"NO recognized section"| G{"Fallback 1:<br/>any bullets<br/>in the whole file?"}

    G -->|"YES"| H["Extract the first 15 bullets"]
    G -->|"NO"| I["Fallback 2:<br/>return the first 5 lines"]

    F --> J["Assemble final DNA"]
    H --> J
    I --> J
    J --> K["Return: structured markdown<br/>~15-30 lines"]
```

### Token cost

| Mode | Average volume | Use case |
|:---|:---|:---|
| DNA (`get_expert_dna`) | ~200-500 tokens | Fast injection, double-pass |
| Full (`load_combo_content`) | ~1000-3000 tokens | Need for complete details |
| × 5 skills DNA | ~1000-2500 tokens | Standard workflow |
| × 5 skills Full | ~5000-15000 tokens | In-depth analysis |

---

## 6. Combo Seeds System

The `config/combos_seed.json` file contains predefined **manual associations**
between task keywords and skill groups that work well together.

```mermaid
flowchart LR
    A["Task: 'Build a React dashboard'"] --> B{"Regex match<br/>in combos_seed.json"}
    B -->|"'React' match!"| C["Combo 'React':<br/>react-specialist<br/>frontend-developer<br/>css-master"]
    B -->|"No match"| D["No expert_combo"]

    C --> E["Added as a BONUS<br/>to suggest_combo result"]
    D --> E
```

### Important
Combo seeds are **complementary**, not exclusive:
- Semantic search always returns its top 5 results
- If a combo seed matches, it is added as a **bonus** (`expert_combo` in the response)
- The LLM can then choose to load the DNA of these bonus skills as well

---

## 7. Recommended Double-Pass Workflow

The MCP is designed to work with the **double-pass** protocol using
Sequential Thinking as an intermediate validator.

```mermaid
sequenceDiagram
    participant U as User
    participant LLM as LLM
    participant ST as Sequential<br/>Thinking
    participant SC as Sequential<br/>Combination
    participant BM as Basic<br/>Memory

    Note over U,BM: === STEP 0: ANCHORING ===
    U->>LLM: Request
    LLM->>BM: Project context?
    BM-->>LLM: Notes, history

    Note over U,BM: === STEP 1: ST PASS 1 (Analysis) ===
    LLM->>ST: Analyze the request<br/>Extract keywords
    ST-->>LLM: Intent: "X"<br/>Keywords: ["a", "b", "c"]

    Note over U,BM: === STEP 2: SKILLS (Loading) ===
    LLM->>SC: suggest_combo("task", "stage", n=5)
    SC-->>LLM: 5 suggested skills

    Note over U,BM: === STEP 3: ST PASS 2 (Validation) ===
    LLM->>ST: Are these 5 skills relevant?<br/>Cross-check with memory context
    ST-->>LLM: Validated: [skill_1, skill_3, skill_5]

    Note over U,BM: === STEP 4: INJECTION ===
    LLM->>SC: get_expert_dna(["skill_1", "skill_3", "skill_5"])
    SC-->>LLM: Injected DNA (rules, methodology)

    Note over U,BM: === STEP 5: RESPONSE ===
    LLM->>U: Response enriched with expertise
```

### Why two passes?

| Pass | Role | Without this pass |
|:---|:---|:---|
| **ST Pass 1** | Understand real intent, not just words | MCP searches for wrong skills |
| **suggest_combo** | Semantic search + stage boost | No expertise loaded |
| **ST Pass 2** | Validate skill relevance | Off-topic skills injected |
| **get_expert_dna** | Surgical rule injection | LLM improvises |

---

## 8. Skill Lifecycle in the Index

```mermaid
flowchart TD
    A["New SKILL.md<br/>added to skills/"] --> B["refresh_index()"]
    B --> C["Read SKILL.md<br/>extract YAML frontmatter"]
    C --> D["SentenceTransformer encodes<br/>text → 384-dimension vector"]
    D --> E["ChromaDB upsert<br/>(id, embedding, metadata, document)"]
    E --> F["Skill available<br/>for search"]

    G["User query"] --> H["query_skills()"]
    H --> I["Encodes query → vector"]
    I --> J["ChromaDB query<br/>cosine distance"]
    J --> K["Stage keyword boost"]
    K --> L["Top N skills returned"]
```

### Metadata stored in ChromaDB details

For each indexed skill, ChromaDB stores:

| Field | Content | Usage |
|:---|:---|:---|
| `id` | Skill folder name | Unique identifier |
| `embedding` | 384-dimension vector | Semantic search |
| `document` | Full SKILL.md content | Keyword matching (boost) |
| `metadata.name` | Skill name (frontmatter) | Display |
| `metadata.description` | Short description | Display |
| `metadata.path` | File path | DNA/full loading |

---

## 9. Technical Summary

| Component | Technology | Role |
|:---|:---|:---|
| Transport | stdio | Standard MCP communication |
| Framework | FastMCP | Python MCP Server |
| Embeddings | SentenceTransformer (MiniLM) | Text → vector (50+ languages) |
| Vector DB | ChromaDB PersistentClient | Storage + cosine search |
| Config | YAML + JSON | Stages and combo seeds |
| Batch size | 100 skills | Batch indexing |

### Key files and their roles

```
server.py         → Entry point, defines the 6 @mcp.tools
skills_index.py   → Engine: indexing, search, DNA extraction
stage_profiles.yaml → Keywords per cognitive stage
combos_seed.json  → Manual task→skills associations
```