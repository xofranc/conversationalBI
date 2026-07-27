from __future__ import annotations

from pathlib import Path
from typing import Optional

from core.knowledge import KnowledgeObject
from core.parser import Graph
from renderers.markdown import MarkdownRenderer
from renderers.mermaid import MermaidRenderer


class ObsidianRenderer:
    def __init__(self, vault_path: Optional[Path] = None) -> None:
        self.vault_path = vault_path
        self.md = MarkdownRenderer()
        self.mermaid = MermaidRenderer()

    def render(self, ko: KnowledgeObject, graph: Optional[Graph] = None) -> str:
        lines: list[str] = []
        lines.append("---")
        lines.append(f'type: {ko.type or "Unknown"}')
        lines.append(f'language: {ko.language or "unknown"}')
        lines.append(f'source: "{ko.source_file}"')
        lines.append(f'tags: [{", ".join(ko.tags)}]')
        lines.append(f'date: {ko.last_updated}')
        lines.append("---")
        lines.append("")
        lines.append(f"# {ko.name}")
        lines.append("")

        if ko.summary:
            lines.append("## Summary")
            lines.append("")
            lines.append(ko.summary)
            lines.append("")

        if ko.purpose:
            lines.append("## Purpose")
            lines.append("")
            lines.append(ko.purpose)
            lines.append("")

        if ko.responsibilities:
            lines.append("## Responsibilities")
            lines.append("")
            for r in ko.responsibilities:
                lines.append(f"- {r}")
            lines.append("")

        if ko.dependencies:
            lines.append("## Dependencies")
            lines.append("")
            for dep in ko.dependencies:
                wiki_link = self._to_wiki_link(dep)
                lines.append(f"- {wiki_link}")
            lines.append("")

        if ko.used_by:
            lines.append("## Used By")
            lines.append("")
            for u in ko.used_by:
                wiki_link = self._to_wiki_link(u)
                lines.append(f"- {wiki_link}")
            lines.append("")

        if ko.calls:
            lines.append("## Calls")
            lines.append("")
            for c in ko.calls:
                wiki_link = self._to_wiki_link(c)
                lines.append(f"- {wiki_link}")
            lines.append("")

        if ko.called_from:
            lines.append("## Called From")
            lines.append("")
            for c in ko.called_from:
                wiki_link = self._to_wiki_link(c)
                lines.append(f"- {wiki_link}")
            lines.append("")

        if ko.source_file:
            lines.append("## Source")
            lines.append("")
            rel_path = ko.source_file
            lines.append(f"`{rel_path}`")
            lines.append("")

        if ko.improvements:
            lines.append("## Suggested Improvements")
            lines.append("")
            for imp in ko.improvements:
                lines.append(f"- {imp}")
            lines.append("")

        if ko.architecture_notes:
            lines.append("## Architecture Notes")
            lines.append("")
            lines.append(ko.architecture_notes)
            lines.append("")

        lines.append("```mermaid")
        lines.append(self.mermaid.render_dependency_graph(ko))
        lines.append("```")
        lines.append("")

        if graph and ko.source_file:
            community = self._find_community(graph, ko.source_file)
            if community is not None:
                lines.append(f"---")
                lines.append(f"*Community: {community}*")

        return "\n".join(lines)

    def render_home(self, knowledge_objects: list[KnowledgeObject], graph: Optional[Graph] = None) -> str:
        lines: list[str] = []

        lines.append("---")
        lines.append('type: home')
        lines.append(f'tags: [knowledge-engine, index]')
        lines.append(f'date: {knowledge_objects[0].last_updated if knowledge_objects else ""}')
        lines.append("---")
        lines.append("")
        lines.append("# Knowledge Base")
        lines.append("")
        lines.append(f"Total entries: {len(knowledge_objects)}")
        lines.append("")

        if graph:
            communities = graph.get_communities()
            lines.append(f"## Architecture Overview ({len(communities)} communities)")
            lines.append("")
            lines.append("```mermaid")
            lines.append(self.mermaid.render_community_graph(graph))
            lines.append("```")
            lines.append("")

        by_type: dict[str, list[KnowledgeObject]] = {}
        for ko in knowledge_objects:
            t = ko.type or "Unknown"
            if t not in by_type:
                by_type[t] = []
            by_type[t].append(ko)

        for node_type in sorted(by_type.keys()):
            lines.append(f"## {node_type}")
            lines.append("")
            for ko in by_type[node_type]:
                wiki_link = self._to_wiki_link(ko.name)
                summary = ko.summary[:120] + "..." if len(ko.summary) > 120 else ko.summary
                lines.append(f"- {wiki_link}")
                if summary:
                    lines.append(f"  - {summary}")
            lines.append("")

        return "\n".join(lines)

    def render_to_vault(self, ko: KnowledgeObject, graph: Optional[Graph] = None) -> Optional[Path]:
        if not self.vault_path:
            return None

        content = self.render(ko, graph)
        node_type = (ko.type or "Unknown").lower()

        type_dirs: dict[str, str] = {
            "model": "Models",
            "view": "Views",
            "service": "Services",
            "serializer": "Serializers",
            "test": "Tests",
            "repository": "Repositories",
            "frontend": "Frontend",
            "config": "Infrastructure",
            "migration": "Infrastructure",
            "admin": "Admin",
            "url": "Infrastructure",
            "app": "Infrastructure",
        }

        subdir = type_dirs.get(node_type, "Modules")
        note_dir = self.vault_path / subdir
        note_dir.mkdir(parents=True, exist_ok=True)

        safe_name = self._safe_filename(ko.name)
        file_path = note_dir / f"{safe_name}.md"
        file_path.write_text(content)
        return file_path

    def render_home_to_vault(self, knowledge_objects: list[KnowledgeObject], graph: Optional[Graph] = None) -> Optional[Path]:
        if not self.vault_path:
            return None

        content = self.render_home(knowledge_objects, graph)
        file_path = self.vault_path / "Home.md"
        file_path.write_text(content)
        return file_path

    @staticmethod
    def _to_wiki_link(name: str) -> str:
        clean = name.replace("(", "").replace(")", "").replace("[", "").replace("]", "").strip()
        return f"[[{clean}]]"

    @staticmethod
    def _safe_filename(name: str) -> str:
        safe = name.replace("/", "_").replace("\\", "_").replace(":", "_").replace(" ", "_")
        safe = "".join(c for c in safe if c.isalnum() or c in "-_.")
        return safe or "unnamed"

    @staticmethod
    def _find_community(graph: Graph, source_file: str) -> Optional[int]:
        for node in graph.nodes:
            if node.source_file == source_file and node.community is not None:
                return node.community
        return None
