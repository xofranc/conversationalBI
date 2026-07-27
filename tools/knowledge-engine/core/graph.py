from __future__ import annotations

from collections import defaultdict
from typing import Optional

from core.parser import Graph, GraphLink, GraphNode


class GraphAnalyzer:
    def __init__(self, graph: Graph) -> None:
        self.graph = graph

    def get_dependencies(self, node_id: str) -> list[GraphNode]:
        deps: list[GraphNode] = []
        seen: set[str] = set()
        for link in self.graph.links:
            if link.source == node_id and link.relation in ("imports_from", "imports", "uses") and link.target not in seen:
                target = self.graph.get_node(link.target)
                if target:
                    deps.append(target)
                    seen.add(link.target)
        return deps

    def get_dependents(self, node_id: str) -> list[GraphNode]:
        deps: list[GraphNode] = []
        seen: set[str] = set()
        for link in self.graph.links:
            if link.target == node_id and link.relation in ("imports_from", "imports", "uses") and link.source not in seen:
                source = self.graph.get_node(link.source)
                if source:
                    deps.append(source)
                    seen.add(link.source)
        return deps

    def get_calls(self, node_id: str) -> list[GraphLink]:
        return [l for l in self.graph.links if l.source == node_id and l.relation == "calls"]

    def get_callers(self, node_id: str) -> list[GraphLink]:
        return [l for l in self.graph.links if l.target == node_id and l.relation == "calls"]

    def get_neighbors_by_relation(self, node_id: str, relation: str) -> list[GraphNode]:
        result: list[GraphNode] = []
        seen: set[str] = set()
        for link in self.graph.links:
            if link.relation != relation:
                continue
            target_id = link.target if link.source == node_id else link.source
            if target_id not in seen:
                node = self.graph.get_node(target_id)
                if node:
                    result.append(node)
                    seen.add(target_id)
        return result

    def get_communities(self) -> dict[Optional[int], list[GraphNode]]:
        return self.graph.get_communities()

    def get_community(self, node_id: str) -> Optional[int]:
        node = self.graph.get_node(node_id)
        return node.community if node else None

    def get_community_nodes(self, community_id: int) -> list[GraphNode]:
        return [n for n in self.graph.nodes if n.community == community_id]

    def get_contained_symbols(self, file_node_id: str) -> list[GraphNode]:
        symbols: list[GraphNode] = []
        for link in self.graph.links:
            if link.source == file_node_id and link.relation == "contains":
                target = self.graph.get_node(link.target)
                if target:
                    symbols.append(target)
        return symbols

    def get_containing_file(self, symbol_id: str) -> Optional[GraphNode]:
        for link in self.graph.links:
            if link.target == symbol_id and link.relation == "contains":
                return self.graph.get_node(link.source)
        return None

    def get_imports(self, node_id: str) -> list[GraphNode]:
        imports: list[GraphNode] = []
        seen: set[str] = set()
        for link in self.graph.links:
            if link.source == node_id and link.relation in ("imports", "imports_from"):
                target = self.graph.get_node(link.target)
                if target and target.id not in seen:
                    imports.append(target)
                    seen.add(target.id)
        return imports

    def build_dependency_graph(self) -> dict[str, list[str]]:
        dep_graph: dict[str, list[str]] = defaultdict(list)
        for link in self.graph.links:
            if link.relation in ("imports_from", "imports", "uses"):
                dep_graph[link.source].append(link.target)
        return dict(dep_graph)

    def find_orphans(self) -> list[GraphNode]:
        connected: set[str] = set()
        for link in self.graph.links:
            connected.add(link.source)
            connected.add(link.target)
        return [n for n in self.graph.nodes if n.id not in connected]

    def find_hubs(self, min_connections: int = 5) -> list[tuple[GraphNode, int]]:
        connection_count: dict[str, int] = defaultdict(int)
        for link in self.graph.links:
            connection_count[link.source] += 1
            connection_count[link.target] += 1
        hubs: list[tuple[GraphNode, int]] = []
        for node_id, count in connection_count.items():
            if count >= min_connections:
                node = self.graph.get_node(node_id)
                if node:
                    hubs.append((node, count))
        return sorted(hubs, key=lambda x: x[1], reverse=True)
