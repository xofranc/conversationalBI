from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Optional

from config import Config
from core.cache import KnowledgeCache
from core.classifier import Classifier
from core.context import ContextBuilder
from core.extractor import CodeExtractor
from core.graph import GraphAnalyzer
from core.knowledge import KnowledgeEngine, KnowledgeObject
from core.llm import LLMConfig, LLMFactory, LLMProvider
from core.parser import GraphParser
from renderers.index import IndexRenderer
from renderers.markdown import MarkdownRenderer
from renderers.mermaid import MermaidRenderer
from renderers.obsidian import ObsidianRenderer


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Knowledge Engine - Transform any repository into an intelligent knowledge base",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  ke --graph graphify-out/graph.json          # Full pipeline
  ke --changed                                # Only changed files
  ke --community 5                            # Process a specific community
  ke --render-only                            # Only render existing knowledge objects
  ke --vault ~/obsidian-vault                 # Render to Obsidian vault
        """,
    )

    parser.add_argument("--graph", type=str, default=None, help="Path to graph.json")
    parser.add_argument("--manifest", type=str, default=None, help="Path to manifest.json")
    parser.add_argument("--output", type=str, default=None, help="Output directory")
    parser.add_argument("--vault", type=str, default=None, help="Obsidian vault path")
    parser.add_argument("--project-root", type=str, default=None, help="Project root directory")

    parser.add_argument("--llm-provider", type=str, default=None, choices=["openai", "anthropic", "claude", "openrouter", "gemini", "kimi", "opencode"])
    parser.add_argument("--llm-model", type=str, default=None, help="LLM model name")
    parser.add_argument("--llm-api-key", type=str, default=None, help="LLM API key")
    parser.add_argument("--llm-api-base", type=str, default=None, help="LLM API base URL")
    parser.add_argument("--no-llm", action="store_true", help="Disable LLM enrichment")

    parser.add_argument("--community", type=int, default=None, help="Process specific community ID")
    parser.add_argument("--changed", action="store_true", help="Only process changed files")
    parser.add_argument("--single", type=str, default=None, help="Process a single file path")
    parser.add_argument("--node-id", type=str, default=None, help="Process a single node by ID")

    parser.add_argument("--render-only", action="store_true", help="Only render existing knowledge objects")
    parser.add_argument("--format", type=str, nargs="+", default=["obsidian"], choices=["markdown", "mermaid", "obsidian", "html", "all"])
    parser.add_argument("--verbose", action="store_true", help="Verbose output")

    return parser.parse_args(argv[1:])


def setup_llm(args: argparse.Namespace, config: Config) -> Optional[LLMProvider]:
    if args.no_llm:
        return None

    llm_config = LLMConfig(
        provider=args.llm_provider or config.llm_provider,
        model=args.llm_model or config.llm_model,
        api_key=args.llm_api_key or config.llm_api_key,
        api_base=args.llm_api_base or config.llm_api_base,
        temperature=config.llm_temperature,
        max_tokens=config.llm_max_tokens,
    )
    return LLMFactory.create(llm_config)


def run_pipeline(args: argparse.Namespace) -> int:
    config = Config.from_env()
    if args.graph:
        config.graph_path = Path(args.graph)
    if args.manifest:
        config.manifest_path = Path(args.manifest)
    if args.output:
        config.output_dir = Path(args.output)
    if args.vault:
        config.obsidian_vault = Path(args.vault)
    if args.project_root:
        config.project_root = Path(args.project_root)
    if args.verbose:
        config.verbose = True

    if args.llm_provider:
        config.llm_provider = args.llm_provider
    if args.llm_model:
        config.llm_model = args.llm_model
    if args.llm_api_key:
        config.llm_api_key = args.llm_api_key
    if args.llm_api_base:
        config.llm_api_base = args.llm_api_base

    config.project_root = config.project_root.resolve()
    config.graph_path = config.graph_path.resolve()
    config.output_dir = config.output_dir.resolve()

    if not config.graph_path.exists():
        print(f"Error: graph file not found: {config.graph_path}", file=sys.stderr)
        print("Run graphify first, or specify --graph path/to/graph.json", file=sys.stderr)
        return 1

    config.ensure_dirs()

    if config.verbose:
        print(f"[KE] Graph: {config.graph_path}")
        print(f"[KE] Output: {config.output_dir}")

    parser = GraphParser(config.graph_path)
    graph = parser.load_graph()

    if config.verbose:
        print(f"[KE] Loaded {len(graph.nodes)} nodes, {len(graph.links)} links")

    project_root = config.project_root

    analyzer = GraphAnalyzer(graph)
    classifier = Classifier()
    extractor = CodeExtractor(project_root=project_root)
    cache = KnowledgeCache(config.cache_dir, project_root=project_root)

    llm_provider = setup_llm(args, config)
    context_builder = ContextBuilder(graph, analyzer, classifier, extractor)

    engine = KnowledgeEngine(
        graph=graph,
        analyzer=analyzer,
        classifier=classifier,
        extractor=extractor,
        cache=cache,
        context_builder=context_builder,
        llm_provider=llm_provider,
        project_root=project_root,
    )

    use_llm = not args.no_llm and llm_provider is not None

    if args.render_only:
        return render_all(graph, engine, config, args)

    if args.single:
        nodes = [n for n in graph.nodes if n.source_file == args.single]
        if not nodes:
            print(f"Error: file not found in graph: {args.single}", file=sys.stderr)
            return 1
        kos = [engine.process_node(nodes[0], use_llm=use_llm)]
    elif args.node_id:
        node = parser.get_node(args.node_id)
        if not node:
            print(f"Error: node not found: {args.node_id}", file=sys.stderr)
            return 1
        kos = [engine.process_node(node, use_llm=use_llm)]
    elif args.community is not None:
        kos = engine.process_community(args.community, use_llm=use_llm)
    elif args.changed:
        kos = engine.process_changed(use_llm=use_llm)
    else:
        kos = engine.process_all(use_llm=use_llm, max_workers=5)

    if config.verbose:
        print(f"[KE] Generated {len(kos)} knowledge objects")

    for ko in kos:
        engine.save_knowledge_object(ko, config.output_dir)
        if config.verbose:
            print(f"[KE] Saved: {ko.name} ({ko.type})")

    arch_kos = engine.get_architecture_knowledge()
    for ako in arch_kos:
        engine.save_knowledge_object(ako, config.output_dir)

    render_all(graph, engine, config, args, kos)

    print(f"\nDone. Output: {config.output_dir}")
    return 0


def render_all(
    graph: Any,
    engine: KnowledgeEngine,
    config: Config,
    args: argparse.Namespace,
    kos: Optional[list[KnowledgeObject]] = None,
) -> None:
    if kos is None:
        kos = []
        nodes_dir = config.nodes_dir
        if nodes_dir.exists():
            for f in sorted(nodes_dir.glob("*.json")):
                ko = engine.load_knowledge_object(f)
                if ko:
                    kos.append(ko)

    formats = args.format if not args.render_only and hasattr(args, "format") else ["all"]
    if "all" in formats:
        formats = ["markdown", "mermaid", "obsidian", "html"]
    if not kos:
        return

    for fmt in formats:
        if fmt == "markdown":
            render_markdown(kos, config)
        elif fmt == "mermaid":
            render_mermaid(kos, config)
        elif fmt == "obsidian":
            render_obsidian(kos, graph, config)
        elif fmt == "html":
            render_html(kos, config)


def render_markdown(kos: list[KnowledgeObject], config: Config) -> None:
    md = MarkdownRenderer()
    md_dir = config.output_dir / "markdown"
    md_dir.mkdir(parents=True, exist_ok=True)

    for ko in kos:
        safe_name = ko.id.replace("/", "_").replace("\\", "_")
        file_path = md_dir / f"{safe_name}.md"
        content = md.render(ko)
        file_path.write_text(content)

    index_content = md.render_index(kos, "Knowledge Base")
    (md_dir / "README.md").write_text(index_content)

    if config.verbose:
        print(f"[KE] Markdown: {md_dir} ({len(kos)} files)")


def render_mermaid(kos: list[KnowledgeObject], config: Config) -> None:
    m = MermaidRenderer()
    mermaid_dir = config.output_dir / "mermaid"
    mermaid_dir.mkdir(parents=True, exist_ok=True)

    for ko in kos:
        safe_name = ko.id.replace("/", "_").replace("\\", "_")
        content = m.render_dependency_graph(ko)
        (mermaid_dir / f"{safe_name}.mmd").write_text(content)

    if len(kos) > 1:
        arch_content = m.render_architecture(kos)
        (mermaid_dir / "architecture.mmd").write_text(arch_content)

    if config.verbose:
        print(f"[KE] Mermaid: {mermaid_dir}")


def render_obsidian(kos: list[KnowledgeObject], graph: Any, config: Config) -> None:
    vault = config.obsidian_vault or (config.output_dir / "obsidian")
    obs = ObsidianRenderer(vault_path=vault)

    for ko in kos:
        obs.render_to_vault(ko, graph)

    obs.render_home_to_vault(kos, graph)

    if config.verbose:
        print(f"[KE] Obsidian: {vault} ({len(kos)} notes)")

    if config.obsidian_vault:
        print(f"[KE] Obsidian vault: {config.obsidian_vault}")


def render_html(kos: list[KnowledgeObject], config: Config) -> None:
    from renderers.html import HTMLRenderer
    html_renderer = HTMLRenderer()
    html_dir = config.output_dir / "html"
    html_dir.mkdir(parents=True, exist_ok=True)

    for ko in kos:
        safe_name = ko.id.replace("/", "_").replace("\\", "_")
        content = html_renderer.render(ko)
        (html_dir / f"{safe_name}.html").write_text(content)

    index_lines: list[str] = [
        "<!DOCTYPE html>",
        '<html lang="en">',
        "<head><meta charset='UTF-8'><title>Knowledge Base</title></head>",
        "<body>",
        "<h1>Knowledge Base</h1>",
        f"<p>Total entries: {len(kos)}</p>",
        "<ul>",
    ]
    for ko in kos:
        safe_name = ko.id.replace("/", "_").replace("\\", "_")
        index_lines.append(f'<li><a href="{safe_name}.html">{ko.name}</a> ({ko.type})</li>')
    index_lines.append("</ul></body></html>")
    (html_dir / "index.html").write_text("\n".join(index_lines))

    if config.verbose:
        print(f"[KE] HTML: {html_dir}")


def main() -> None:
    import sys
    args = parse_args(sys.argv)
    sys.exit(run_pipeline(args))


if __name__ == "__main__":
    main()
