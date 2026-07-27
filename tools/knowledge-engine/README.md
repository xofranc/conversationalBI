# Knowledge Engine

Transform any software repository into an intelligent knowledge base.

## Flow

```
Repository → Graphify → graph.json → Knowledge Engine → Knowledge Objects (JSON) → LLM → Renderers → Obsidian / AI Context
```

## Installation

```bash
cd tools/knowledge-engine
pip install -e .
```

## Usage

```bash
# Full pipeline (requires graph.json from Graphify)
ke

# Without LLM enrichment
ke --no-llm

# Output to specific directory
ke --output ./knowledge-out

# Render to Obsidian vault
ke --vault ~/my-vault

# Only process changed files
ke --changed

# Process single community
ke --community 5

# All render formats
ke --format all

# With OpenAI
ke --llm-provider openai --llm-model gpt-4o --llm-api-key sk-...

# With Anthropic Claude
ke --llm-provider anthropic --llm-model claude-sonnet-4-20250514 --llm-api-key sk-...
```

## Architecture

```
knowledge-engine/
├── main.py              # CLI entry point
├── config.py            # Configuration management
├── core/
│   ├── parser.py        # Graph.json interpreter
│   ├── graph.py         # Relationship analysis
│   ├── classifier.py    # Node type classification
│   ├── extractor.py     # Source code extraction (AST + regex)
│   ├── cache.py         # Hash-based incremental caching
│   ├── context.py       # LLM context builder
│   ├── llm.py           # Provider-agnostic LLM interface
│   └── knowledge.py     # Knowledge Object engine (core)
├── renderers/
│   ├── markdown.py      # Markdown renderer
│   ├── mermaid.py       # Mermaid diagram renderer
│   ├── obsidian.py      # Obsidian vault renderer
│   ├── html.py          # HTML renderer
│   └── index.py         # Multi-format index renderer
├── knowledge/
│   └── schema.json      # Knowledge Object schema
├── pyproject.toml
└── README.md
```

## Module Responsibilities

| Module | Role |
|--------|------|
| `parser.py` | Loads graph.json — never calls LLM, never generates docs |
| `graph.py` | Analyzes relationships (dependencies, calls, communities) |
| `classifier.py` | Classifies nodes (Model, View, Service, etc.) by filename |
| `extractor.py` | Extracts classes, functions, docstrings without AI |
| `cache.py` | Avoids redundant LLM calls via SHA-256 hashing |
| `llm.py` | Provider-agnostic LLM interface (OpenAI, Claude, Gemini, etc.) |
| `knowledge.py` | Orchestrates Knowledge Object creation |
| Renderers | Convert Knowledge Objects to output formats — never analyze code, never call LLM |
