# 📝 SKILL Writing Guide

How to structure a `SKILL.md` file so that `sequential-combination` can extract the best DNA.

---

## Why Does This Matter?

The `get_expert_dna` tool extracts only the **core rules and methodology** from your `SKILL.md`.
It searches for specific section headers and bullet points. If your file doesn't have them,
the DNA extraction will fall back to generic bullet points — much less useful.

---

## Sections Recognized by the DNA Extractor

The extractor looks for these section headers (case-insensitive):

| Header | What it captures |
|:---|:---|
| `## Instructions` / `## Core Instructions` | Step-by-step process |
| `## Rules` / `## Core Rules` | Hard constraints and must-dos |
| `## Methodology` | The approach and strategy |
| `## Directives` | Behavioral guidelines |
| `## Principles` / `## Core` | Foundational concepts |
| `## Best Practices` | Recommended patterns |
| `## When to Use` | Conditions for activation |

---

## Recommended SKILL.md Structure

```markdown
---
name: my-awesome-skill
description: "Brief description of what this skill does"
---

# My Awesome Skill

## When to Use
- When the user asks for X
- When the task involves Y

## Core Instructions
- Always do A before B
- Never skip validation step

## Methodology
1. Analyze the input
2. Apply pattern matching
3. Generate output following rules

## Rules
- ✅ DO: use typed parameters
- ❌ DON'T: hardcode values
- ✅ DO: validate all inputs
- ❌ DON'T: skip error handling

## Best Practices
- Prefer composition over inheritance
- Keep functions under 20 lines
- Document all public APIs
```

---

## Tips for Maximum DNA Quality

1. **Use bullet points** (-, *, •) — the DNA extractor captures them, not paragraphs.
2. **Use ✅ DO / ❌ DON'T lists** — very effective for injecting guardrails.
3. **Keep headings standard** — use the exact names from the table above.
4. **Cap sections at 20 items** — the extractor limits to 20 bullets per section.
5. **Frontmatter is required** — include `name` and `description` in YAML.

---

## What Happens Without These Sections?

If no recognized sections are found:
1. The extractor searches for **any bullet points** in the file (fallback).
2. If nothing is found at all, it returns the **first 5 lines** of the file.

This fallback produces poor DNA. Structure your SKILL.md properly.
