# 🧬 Sequential Combination MCP

> Semantic skill search and expertise injection for LLMs.
> Built for the [antigravity-awesome-skills](https://github.com/sickn33/antigravity-awesome-skills) repository (1200+ skills).

---

## Table of Contents

- [What it does](#what-it-does)
- [Installation](#installation)
- [Configuration](#configuration)
- [Tools Reference](#tools-reference)
- [Workflow — Double-Passe Protocol](#workflow--double-passe-protocol)
- [Stage Profiles](#stage-profiles)
- [Combo Seeds](#combo-seeds)
- [Writing a SKILL.md](#writing-a-skillmd)
- [Architecture](#architecture)
- [Contributing](#contributing)
- [License](#license)

---

## What it does

Sequential Combination is an MCP server that:
1. **Indexes** 1200+ skill files from `antigravity-awesome-skills` using ChromaDB vector embeddings
2. **Searches** relevant skills for any task using semantic similarity (multilingual)
3. **Injects** the core expertise (DNA) or full content into the LLM's context

The embedding model (`paraphrase-multilingual-MiniLM-L12-v2`) supports **50+ languages** — search works
regardless of the language of the query or the SKILL.md file.

---

## Installation

### Prerequisites
- Python 3.10+
- Git

### Step 1: Clone the repository
```bash
git clone https://github.com/YOUR_USERNAME/sequential-combination.git
cd sequential-combination/new-combination
```

### Step 2: Create virtual environment and install dependencies
```bash
python -m venv .venv

# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate

pip install -r requirements.txt
```

### Step 3: Link your skills directory
The server expects a `skills/` directory containing the antigravity-awesome-skills:
```bash
# Option A: Symbolic link (recommended)
# Windows (PowerShell as Admin)
New-Item -ItemType SymbolicLink -Path ".\skills" -Target "C:\path\to\antigravity-awesome-skills"

# macOS/Linux
ln -s /path/to/antigravity-awesome-skills ./skills
```

```bash
# Option B: Clone directly
git clone https://github.com/sickn33/antigravity-awesome-skills.git skills
```

### Step 4: Add to your MCP config
Add this entry to your `mcp_config.json`:
```json
{
  "sequential-combination": {
    "command": "python",
    "args": ["src/server.py"],
    "cwd": "/path/to/new-combination",
    "transport": "stdio"
  }
}
```

### Step 5: Start the server
```bash
python src/server.py
```
You should see:
```
Starting Sequential Combination MCP Server...
Loading SentenceTransformer model...
SkillsIndexer ready.
```

---

## Configuration

### Skills Directory
The `skills/` folder must contain subdirectories, each with a `SKILL.md` file:
```
skills/
├── css-master/
│   └── SKILL.md
├── api-security-best-practices/
│   └── SKILL.md
└── ...
```

### Stage Profiles (`config/stage_profiles.yaml`)
Defines which keywords boost relevance for each cognitive stage.
Edit to add custom stages or keywords.

### Combo Seeds (`config/combos_seed.json`)
Pre-defined skill bundles that auto-trigger when a task matches.
Add your own cross-domain combos for recurring use cases.

---

## Tools Reference

| Tool | Description | Token Cost |
|:---|:---|:---|
| `list_stages` | List cognitive stages from `stage_profiles.yaml` | Minimal |
| `suggest_combo(task, stage, n=5)` | Semantic search for best skills at a given stage | Low |
| `get_expert_dna(skills)` | Extract condensed rules/methodology (surgical) | **Low** ✅ |
| `load_combo_content(skills)` | Load targeted sections from SKILL.md files | Medium |
| `suggest_and_inject(task, stage, mode, n)` | Combined: suggest + inject in one call | Depends on mode |
| `ping` | Health check | Minimal |

### Usage Examples

**Quick injection (one call):**
```python
# suggest_and_inject finds the best 5 skills and injects their DNA
result = await suggest_and_inject("secure REST API with JWT", "Synthesis", mode="dna", n=5)
print(result["injected_content"])  # → Core rules from 5 expert skills
```

**Advanced workflow (double-passe protocol):**
```python
# Step 1: Suggest skills for current stage
skills = await suggest_combo("secure REST API with JWT", "Analysis", n=5)

# Step 2: Validate with Sequential Thinking (separate MCP)
#         → ST decides which skills are truly relevant

# Step 3: Extract DNA for validated skills
dna = await get_expert_dna(["api-security-best-practices", "backend-security-coder"])
```

---

## Workflow — Double-Passe Protocol

The recommended workflow when using this MCP with Sequential Thinking:

```
┌─────────────────────────────────────────────────────────┐
│ For EACH cognitive stage (Problem → Research → ...)     │
│                                                         │
│  1. suggest_combo(task, stage)                          │
│       ↓                                                 │
│  2. Sequential Thinking validates skill relevance       │
│       ↓                                                 │
│  3. get_expert_dna(validated_skills)                    │
│       ↓                                                 │
│  4. LLM uses injected expertise to produce output       │
│       ↓                                                 │
│  5. Move to next stage, repeat                          │
└─────────────────────────────────────────────────────────┘
```

The key principle: **each cognitive stage gets its own set of experts**.
A task about "building a crypto trading platform" will receive:
- **Problem stage**: security, crypto-wallet, constraint-analysis skills
- **Research stage**: market-research, trend-analysis skills
- **Analysis stage**: async-python, fastapi-development skills
- **Synthesis stage**: frontend-developer, architecture skills
- **Conclusion stage**: documentation, deployment skills

---

## Stage Profiles

Defined in `config/stage_profiles.yaml`. Each stage has keywords that boost
relevance when matching skills:

| Stage | Keywords |
|:---|:---|
| Problem | analysis, audit, debug, diagnostic, review, issue, bug, constraint, requirement, error |
| Research | search, scraping, fetch, discovery, data, web, trend, market, survey, find, explore |
| Analysis | compare, critique, evaluate, benchmark, testing, performance, security, architecture, assess |
| Synthesis | writing, structuring, architecture, design, planning, implementation, coding, build, create |
| Conclusion | reporting, summary, documentation, output, deploy, publish, release, finalize |

---

## Combo Seeds

Pre-defined skill bundles in `config/combos_seed.json` that auto-trigger
when a task matches their name. These are **complementary** to the semantic
search — both results are returned.

---

## Writing a SKILL.md

See [SKILL_WRITING_GUIDE.md](./SKILL_WRITING_GUIDE.md) for detailed instructions on how to
structure your skill files for optimal DNA extraction.

---

## Architecture

```
new-combination/
├── src/
│   ├── server.py            ← FastMCP server, 6 tools, stdio transport
│   └── skills_index.py      ← Vector search engine + DNA extraction
├── config/
│   ├── combos_seed.json     ← Pre-defined skill bundles
│   └── stage_profiles.yaml  ← Cognitive stage keyword profiles
├── skills/                  ← Symlink to antigravity-awesome-skills
├── data/chroma_db/          ← ChromaDB vector database (auto-created)
├── SKILL_WRITING_GUIDE.md   ← How to write SKILL.md files
├── requirements.txt         ← Python dependencies
└── README.md                ← This file
```

### Key Technologies
- **FastMCP** — MCP server framework (stdio transport)
- **SentenceTransformer** — `paraphrase-multilingual-MiniLM-L12-v2` for 50+ language support
- **ChromaDB** — Vector database for semantic search (cosine similarity)
- **PyYAML** — Stage profile configuration

---

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## License

MIT License — see [LICENSE](./LICENSE) for details.
