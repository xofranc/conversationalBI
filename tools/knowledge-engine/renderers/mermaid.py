from __future__ import annotations

from typing import Optional

from core.knowledge import KnowledgeObject
from core.parser import Graph


class MermaidRenderer:
    def render_dependency_graph(self, ko: KnowledgeObject) -> str:
        lines: list[str] = ["graph TD"]
        lines.append(f"  {self._safe_id(ko.name)}[\"{ko.name}\"]")

        for dep in ko.dependencies:
            dep_id = self._safe_id(dep)
            lines.append(f"  {dep_id}[\"{dep}\"]")
            lines.append(f"  {self._safe_id(ko.name)} --> {dep_id}")

        for u in ko.used_by:
            u_id = self._safe_id(u)
            lines.append(f"  {u_id}[\"{u}\"]")
            lines.append(f"  {u_id} --> {self._safe_id(ko.name)}")

        return "\n".join(lines)

    def render_class_diagram(self, ko: KnowledgeObject) -> str:
        if ko.type not in ("Model", "Class"):
            return self.render_dependency_graph(ko)

        lines: list[str] = ["classDiagram"]
        class_name = self._safe_class_name(ko.name)
        lines.append(f"  class {class_name} {{")

        for resp in ko.responsibilities:
            clean = resp.replace('"', "'")
            lines.append(f"    +{clean}")

        for out in ko.outputs:
            clean = out.replace('"', "'")
            lines.append(f"    +{clean}")

        lines.append("  }")

        for dep in ko.dependencies:
            dep_name = self._safe_class_name(dep)
            lines.append(f"  {class_name} --> {dep_name}")

        for u in ko.used_by:
            u_name = self._safe_class_name(u)
            lines.append(f"  {u_name} --> {class_name}")

        return "\n".join(lines)

    def render_flowchart(self, ko: KnowledgeObject) -> str:
        lines: list[str] = ["flowchart LR"]
        lines.append(f"  {self._safe_id(ko.name)}[{ko.name}]")

        for dep in ko.dependencies:
            dep_id = self._safe_id(dep)
            lines.append(f"  {dep_id}[{dep}]")
            lines.append(f"  {self._safe_id(ko.name)} -->|depends on| {dep_id}")

        for c in ko.calls:
            c_id = self._safe_id(c)
            if c_id != self._safe_id(ko.name):
                lines.append(f"  {c_id}[{c}]")
                lines.append(f"  {self._safe_id(ko.name)} -->|calls| {c_id}")

        return "\n".join(lines)

    def render_architecture(self, knowledge_objects: list[KnowledgeObject]) -> str:
        lines: list[str] = ["graph TB"]
        subgraphs: dict[str, list[str]] = {}

        for ko in knowledge_objects:
            t = ko.type or "Unknown"
            if t not in subgraphs:
                subgraphs[t] = []
            subgraphs[t].append(self._safe_id(ko.name))

        for idx, (node_type, node_ids) in enumerate(sorted(subgraphs.items())):
            lines.append(f"  subgraph {node_type}[{node_type}]")
            for nid in node_ids:
                lines.append(f"    {nid}")
            lines.append("  end")

        seen_links: set[str] = set()
        for ko in knowledge_objects:
            for dep in ko.dependencies:
                dep_id = self._safe_id(dep)
                src_id = self._safe_id(ko.name)
                link = f"{src_id} --> {dep_id}"
                if link not in seen_links and src_id != dep_id:
                    lines.append(f"  {link}")
                    seen_links.add(link)

        return "\n".join(lines)

    def render_community_graph(self, graph: Graph) -> str:
        communities = graph.get_communities()
        lines: list[str] = ["graph TB"]

        for comm_id, nodes in communities.items():
            safe_comm = f"comm_{comm_id}" if comm_id is not None else "comm_none"
            file_nodes = [n for n in nodes if n.is_file_node and n.source_file]
            if not file_nodes:
                continue
            label = f"Community {comm_id}" if comm_id is not None else "Unclassified"
            lines.append(f"  subgraph {safe_comm}[\"{label}\"]")
            for node in file_nodes[:15]:
                nid = self._safe_id(node.id)
                lines.append(f"    {nid}[\"{node.label}\"]")
            lines.append("  end")

        for link in graph.links:
            if link.relation == "imports_from":
                src = self._safe_id(link.source)
                tgt = self._safe_id(link.target)
                lines.append(f"  {src} -.-> {tgt}")

        return "\n".join(lines)

    @staticmethod
    def _safe_id(name: str) -> str:
        safe = "".join(c if c.isalnum() else "_" for c in name)
        if safe and safe[0].isdigit():
            safe = "_" + safe
        return safe or "_"

    @staticmethod
    def _safe_class_name(name: str) -> str:
        clean = name.replace("(", "").replace(")", "").replace(" ", "_")
        clean = "".join(c for c in clean if c.isalnum() or c == "_")
        return clean or "Unknown"
