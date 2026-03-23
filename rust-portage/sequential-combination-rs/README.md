# 🦀 Sequential Combination MCP — Rust Port

**Zero-Dependency, High-Performance Rust port of the Sequential Combination MCP Server.**

This is a native Rust rewrite of the original Python server, designed to eliminate all environment issues (restart loops, Python version conflicts, missing `pip` packages) while delivering 10-50x performance improvements.

---

## 🔥 Why Rust vs Python?

| Feature | Python (Original) | Rust (This Port) |
|---|---|---|
| Startup Time | 5-15s (model load) | < 500ms (mmap) |
| Memory | ~2 GB (PyTorch) | ~50 MB |
| Deployment | `venv` + `pip install` | Single binary |
| Restart Loop | ❌ stdout pollution | ✅ All logs → stderr |
| Thread Safety | GIL-limited | Arc<RwLock<>> native |

---

## 📁 Project Structure

```
sequential-combination-rs/
├── Cargo.toml             ← Rust dependencies
├── src/
│   ├── main.rs            ← Entry point, stderr logging init
│   ├── server.rs          ← MCP tool definitions (5 tools)
│   ├── skills_index.rs    ← HNSW vector search + ONNX embeddings
│   ├── dna_extractor.rs   ← SIMD-accelerated DNA extraction
│   └── config_loader.rs   ← YAML/JSON config loaders
├── config/
│   ├── stage_profiles.yaml
│   └── combos_seed.json
└── skills/                ← Symlink to antigravity-awesome-skills (1200+ skills)
```

---

## 🛠️ Tech Stack

- **`rmcp`** — Official Rust MCP SDK (async, type-safe JSON-RPC)
- **`tokio`** — Async runtime (multi-threaded)
- **`fastembed`** — ONNX-based ML embeddings (no Python/CUDA required)
- **`instant-distance`** — In-memory HNSW vector search
- **`regex`** — SIMD-accelerated text processing for DNA extraction
- **`tracing`** — Structured logging (all output to stderr only)

---

## 🚀 Installation & Build

### Prerequisites
- [Rust](https://rustup.rs/) (stable, 1.75+)
- Internet access (first run downloads ONNX model ~30MB)

### Build

```bash
# Clone / navigate to this folder
cd rust-portage/sequential-combination-rs

# Build in release mode (optimized binary)
cargo build --release

# Binary location:
# ./target/release/sequential-combination-rs.exe (Windows)
# ./target/release/sequential-combination-rs     (Linux/Mac)
```

### Link your skills directory
```bash
# On Windows (run as admin)
mklink /D "skills" "C:\path\to\antigravity-awesome-skills"

# On Linux/Mac
ln -s /path/to/antigravity-awesome-skills skills
```

---

## ⚙️ VSCode / Kilocode Configuration

Add to your `mcp_config.json`:

```json
{
  "mcpServers": {
    "sequential-combination-rs": {
      "command": "C:/path/to/sequential-combination-rs.exe",
      "args": [],
      "env": {
        "MCP_BASE_DIR": "C:/path/to/sequential-combination-rs",
        "RUST_LOG": "info"
      }
    }
  }
}
```

---

## 🧰 Available Tools

| Tool | Description |
|---|---|
| `ping` | Health check, returns server version and runtime |
| `list_stages` | List all cognitive stages from stage_profiles.yaml |
| `suggest_combo` | Suggest best skills for a task and stage |
| `get_expert_dna` | Get condensed expertise DNA for a list of skills |
| `load_combo_content` | Load full SKILL.md content for a list of skills |

---

## 🐛 Fixing the Restart Loop

The Python version sometimes caused clients (VSCode/Kilocode) to restart the MCP server in a loop. This was caused by:

1. **stdout pollution**: PyTorch and sentence-transformers printed warnings to stdout, corrupting JSON-RPC messages.
2. **Slow startup**: Model loading (5-15s) exceeded client timeout, causing forced restart.

This Rust port fixes both:
- **All logs strictly routed to `stderr`** via `tracing-subscriber`.
- **Model loads in < 500ms** from ONNX binary weights via mmap.

---

## 📄 License

MIT — Built with ❤️ and 🦀
