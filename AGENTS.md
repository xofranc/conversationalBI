## graphify

This project has a knowledge graph at graphify-out/ with god nodes, community structure, and cross-file relationships.

When the user types `/graphify`, use the installed graphify skill or instructions before doing anything else.

Rules:
- For codebase questions, first run `graphify query "<question>"` when graphify-out/graph.json exists. Use `graphify path "<A>" "<B>"` for relationships and `graphify explain "<concept>"` for focused concepts. These return a scoped subgraph, usually much smaller than GRAPH_REPORT.md or raw grep output.
- Dirty graphify-out/ files are expected after hooks or incremental updates; dirty graph files are not a reason to skip graphify. Only skip graphify if the task is about stale or incorrect graph output, or the user explicitly says not to use it.
- If graphify-out/wiki/index.md exists, use it for broad navigation instead of raw source browsing.
- Read graphify-out/GRAPH_REPORT.md only for broad architecture review or when query/path/explain do not surface enough context.
- After modifying code, run `graphify update .` to keep the graph current (AST-only, no API cost).

## knowledge-engine

This project uses Knowledge Engine (tools/knowledge-engine/) to transform the Graphify graph into an intelligent knowledge base in the Obsidian vault (vault/).

When the user types `/ke`, run the knowledge engine to update the vault:
- `ke --changed --no-llm` — incremental update (only changed files)
- `ke --no-llm` — full regeneration
- `ke --llm-provider openai --llm-model ...` — with LLM enrichment (requires KE_LLM_API_KEY)
- `ke --community 5 --no-llm` — single community
- `ke --single backend/apps/dataset/models.py --no-llm` — single file

Before answering codebase questions, first check vault/Home.md for the index. Use the vault as primary context for architecture understanding, then fall back to graphify for specific queries.
