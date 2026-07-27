from __future__ import annotations

from typing import Optional

from core.classifier import Classifier, NodeType
from core.extractor import CodeExtractor, ModuleInfo
from core.graph import GraphAnalyzer
from core.parser import Graph, GraphNode


class ContextBuilder:
    def __init__(self, graph: Graph, analyzer: GraphAnalyzer, classifier: Classifier, extractor: CodeExtractor) -> None:
        self.graph = graph
        self.analyzer = analyzer
        self.classifier = classifier
        self.extractor = extractor

    def build_node_context(self, node: GraphNode) -> str:
        parts: list[str] = []
        parts.append(f"# Node: {node.label}")
        parts.append(f"- ID: {node.id}")
        parts.append(f"- Type: {self.classifier.classify(node).value}")
        parts.append(f"- File: {node.source_file}")
        parts.append(f"- Location: {node.source_location}")
        parts.append(f"- Community: {node.community}")

        if node.source_file:
            subgraph = self._build_subgraph(node)
            if subgraph:
                parts.append(f"\n## Relationships\n{subgraph}")

        return "\n".join(parts)

    def build_subgraph_context(self, node_ids: list[str], max_depth: int = 2) -> str:
        seen: set[str] = set()
        parts: list[str] = []
        for node_id in node_ids:
            self._build_subgraph_recursive(node_id, seen, parts, depth=0, max_depth=max_depth)
        return "\n".join(parts)

    def _build_subgraph(self, node: GraphNode) -> str:
        lines: list[str] = []
        neighbors = self.graph.get_neighbors(node.id)
        if neighbors:
            lines.append(f"- Neighbors ({len(neighbors)}):")
            for n in neighbors[:20]:
                ntype = self.classifier.classify(n).value
                lines.append(f"  - {n.label} ({ntype}) [{n.id}]")

        outgoing = self.graph.get_outgoing_links(node.id)
        imports = [l for l in outgoing if l.relation in ("imports", "imports_from")]
        if imports:
            lines.append(f"- Imports ({len(imports)}):")
            for l in imports[:15]:
                target = self.graph.get_node(l.target)
                if target:
                    lines.append(f"  - {target.label}")

        calls = [l for l in outgoing if l.relation == "calls"]
        if calls:
            lines.append(f"- Calls ({len(calls)}):")
            for l in calls[:15]:
                target = self.graph.get_node(l.target)
                if target:
                    lines.append(f"  - {target.label}")

        incoming = self.graph.get_incoming_links(node.id)
        callers = [l for l in incoming if l.relation == "calls"]
        if callers:
            lines.append(f"- Called by ({len(callers)}):")
            for l in callers[:10]:
                source = self.graph.get_node(l.source)
                if source:
                    lines.append(f"  - {source.label}")

        return "\n".join(lines)

    def _build_subgraph_recursive(self, node_id: str, seen: set[str], parts: list[str], depth: int, max_depth: int) -> None:
        if node_id in seen or depth > max_depth:
            return
        seen.add(node_id)
        node = self.graph.get_node(node_id)
        if not node:
            return

        indent = "  " * depth
        parts.append(f"{indent}- {node.label} [{node.id}]")
        if depth < max_depth:
            for link in self.graph.get_outgoing_links(node_id):
                self._build_subgraph_recursive(link.target, seen, parts, depth + 1, max_depth)

    def build_llm_enrichment_prompt(self, node: GraphNode, module_info: Optional[ModuleInfo] = None) -> str:
        node_type = self.classifier.classify(node).value
        lines: list[str] = [
            "You are a senior software architect. Analyze the following code element and return a JSON object.",
            "",
            f"## Element: {node.label}",
            f"- Type: {node_type}",
            f"- File: {node.source_file}",
            f"- Location: {node.source_location}",
            "",
            "### Relationships",
        ]

        rels = self._build_subgraph(node)
        lines.append(rels)

        if module_info:
            lines.append("")
            lines.append("### Source Code Structure")
            if module_info.docstring:
                lines.append(f"Module docstring: {module_info.docstring[:500]}")
            if module_info.classes:
                lines.append(f"Classes: {', '.join(c.name for c in module_info.classes)}")
            if module_info.functions:
                lines.append(f"Functions: {', '.join(f.name for f in module_info.functions)}")
            if module_info.imports:
                lines.append(f"Imports: {', '.join(module_info.imports[:30])}")

        lines.append("")
        lines.append("""Return ONLY valid JSON with this structure:
{
  "summary": "One-line summary of what this element does",
  "purpose": "Why this element exists and what problem it solves",
  "responsibilities": ["responsibility1", "responsibility2"],
  "inputs": ["input1"],
  "outputs": ["output1"],
  "architecture_notes": "Architectural role, patterns used, design decisions",
  "improvements": ["suggested improvement1"]
}""")

        return "\n".join(lines)

    def build_architecture_context(self) -> str:
        communities = self.graph.get_communities()
        lines: list[str] = ["# Project Architecture Overview", ""]

        for comm_id in sorted(communities.keys(), key=lambda k: k or 0):
            nodes = communities[comm_id]
            types: dict[str, int] = {}
            for n in nodes:
                t = self.classifier.classify(n).value
                types[t] = types.get(t, 0) + 1

            file_nodes = [n for n in nodes if n.is_file_node and n.source_file]
            lines.append(f"## Community {comm_id}")
            lines.append(f"- Total nodes: {len(nodes)}")
            lines.append(f"- Composition: {types}")
            if file_nodes:
                lines.append(f"- Key files: {', '.join(n.source_file for n in file_nodes[:10])}")
            lines.append("")

        return "\n".join(lines)
