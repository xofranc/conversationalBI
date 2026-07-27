from __future__ import annotations

from pathlib import Path
from typing import Optional

from core.knowledge import KnowledgeObject
from core.parser import Graph
from renderers.markdown import MarkdownRenderer
from renderers.mermaid import MermaidRenderer
from renderers.obsidian import ObsidianRenderer
from renderers.html import HTMLRenderer


class IndexRenderer:
    def __init__(self, output_dir: Path, vault_path: Optional[Path] = None):
        self.output_dir = output_dir
        self.vault_path = vault_path
        self.md = MarkdownRenderer()
        self.mermaid = MermaidRenderer()
        self.obsidian = ObsidianRenderer(vault_path=vault_path)
        self.html = HTMLRenderer()

    def render_all(self, kos: list[KnowledgeObject], graph: Optional[Graph] = None) -> int:
        count = 0
        if kos:
            count += self._render_markdown(kos)
            count += self._render_mermaid(kos)
            count += self._render_obsidian(kos, graph)
            count += self._render_html(kos)
        return count

    def _render_markdown(self, kos: list[KnowledgeObject]) -> int:
        md_dir = self.output_dir / "markdown"
        md_dir.mkdir(parents=True, exist_ok=True)
        for ko in kos:
            safe_name = ko.id.replace("/", "_").replace("\\", "_")
            (md_dir / f"{safe_name}.md").write_text(self.md.render(ko))
        (md_dir / "README.md").write_text(self.md.render_index(kos))
        return len(kos)

    def _render_mermaid(self, kos: list[KnowledgeObject]) -> int:
        mermaid_dir = self.output_dir / "mermaid"
        mermaid_dir.mkdir(parents=True, exist_ok=True)
        for ko in kos:
            safe_name = ko.id.replace("/", "_").replace("\\", "_")
            (mermaid_dir / f"{safe_name}.mmd").write_text(self.mermaid.render_dependency_graph(ko))
        if len(kos) > 1:
            (mermaid_dir / "architecture.mmd").write_text(self.mermaid.render_architecture(kos))
        return len(kos)

    def _render_obsidian(self, kos: list[KnowledgeObject], graph: Optional[Graph] = None) -> int:
        vault = self.vault_path or (self.output_dir / "obsidian")
        obs = ObsidianRenderer(vault_path=vault)
        count = 0
        for ko in kos:
            if obs.render_to_vault(ko, graph):
                count += 1
        obs.render_home_to_vault(kos, graph)
        return count

    def _render_html(self, kos: list[KnowledgeObject]) -> int:
        html_dir = self.output_dir / "html"
        html_dir.mkdir(parents=True, exist_ok=True)
        for ko in kos:
            safe_name = ko.id.replace("/", "_").replace("\\", "_")
            (html_dir / f"{safe_name}.html").write_text(self.html.render(ko))
        return len(kos)
