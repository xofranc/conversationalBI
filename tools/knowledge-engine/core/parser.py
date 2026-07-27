from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional


class GraphNode:
    def __init__(self, data: dict[str, Any]) -> None:
        self.id: str = data.get("id", "")
        self.label: str = data.get("label", "")
        self.norm_label: str = data.get("norm_label", "")
        self.file_type: str = data.get("file_type", "")
        self.source_file: str = data.get("source_file", "")
        self.source_location: str = data.get("source_location", "")
        self.community: Optional[int] = data.get("community")
        self.origin: str = data.get("_origin", "")
        self.raw: dict[str, Any] = data

    @property
    def is_file_node(self) -> bool:
        return bool(self.source_file) and not self.source_location or self.source_location == "L1"

    @property
    def is_symbol_node(self) -> bool:
        return bool(self.source_file) and self.source_location and self.source_location != "L1"

    def __repr__(self) -> str:
        return f"GraphNode(id={self.id}, label={self.label})"


class GraphLink:
    def __init__(self, data: dict[str, Any]) -> None:
        self.source: str = data.get("source", "")
        self.target: str = data.get("target", "")
        self.relation: str = data.get("relation", "")
        self.context: Optional[str] = data.get("context")
        self.weight: float = data.get("weight", 1.0)
        self.confidence: str = data.get("confidence", "")
        self.source_file: Optional[str] = data.get("source_file")
        self.source_location: Optional[str] = data.get("source_location")
        self.raw: dict[str, Any] = data

    def __repr__(self) -> str:
        return f"GraphLink({self.source} --[{self.relation}]--> {self.target})"


class Graph:
    def __init__(self, raw: dict[str, Any]) -> None:
        self.raw = raw
        self.directed: bool = raw.get("directed", False)
        self.multigraph: bool = raw.get("multigraph", False)
        self.built_at_commit: Optional[str] = raw.get("built_at_commit")
        self._nodes: list[GraphNode] = [GraphNode(n) for n in raw.get("nodes", [])]
        self._links: list[GraphLink] = [GraphLink(l) for l in raw.get("links", [])]
        self._node_map: dict[str, GraphNode] = {n.id: n for n in self._nodes}

    @property
    def nodes(self) -> list[GraphNode]:
        return self._nodes

    @property
    def links(self) -> list[GraphLink]:
        return self._links

    def get_node(self, node_id: str) -> Optional[GraphNode]:
        return self._node_map.get(node_id)

    def get_links_for(self, node_id: str) -> list[GraphLink]:
        return [l for l in self._links if l.source == node_id or l.target == node_id]

    def get_outgoing_links(self, node_id: str) -> list[GraphLink]:
        return [l for l in self._links if l.source == node_id]

    def get_incoming_links(self, node_id: str) -> list[GraphLink]:
        return [l for l in self._links if l.target == node_id]

    def get_neighbors(self, node_id: str) -> list[GraphNode]:
        neighbors: list[GraphNode] = []
        seen: set[str] = set()
        for link in self._links:
            if link.source == node_id and link.target not in seen:
                neighbor = self._node_map.get(link.target)
                if neighbor:
                    neighbors.append(neighbor)
                    seen.add(link.target)
            elif link.target == node_id and link.source not in seen:
                neighbor = self._node_map.get(link.source)
                if neighbor:
                    neighbors.append(neighbor)
                    seen.add(link.source)
        return neighbors

    def get_file_nodes(self) -> list[GraphNode]:
        return [n for n in self._nodes if n.is_file_node and n.source_file]

    def get_symbol_nodes(self) -> list[GraphNode]:
        return [n for n in self._nodes if n.is_symbol_node]

    def get_communities(self) -> dict[Optional[int], list[GraphNode]]:
        communities: dict[Optional[int], list[GraphNode]] = {}
        for node in self._nodes:
            comm = node.community
            if comm not in communities:
                communities[comm] = []
            communities[comm].append(node)
        return communities


class GraphParser:
    def __init__(self, graph_path: Path) -> None:
        self.graph_path = graph_path
        self._graph: Optional[Graph] = None

    def load_graph(self) -> Graph:
        if self._graph is not None:
            return self._graph
        with open(self.graph_path, "r") as f:
            raw = json.load(f)
        self._graph = Graph(raw)
        return self._graph

    def get_nodes(self) -> list[GraphNode]:
        return self.load_graph().nodes

    def get_links(self) -> list[GraphLink]:
        return self.load_graph().links

    def get_neighbors(self, node_id: str) -> list[GraphNode]:
        return self.load_graph().get_neighbors(node_id)

    def get_node(self, node_id: str) -> Optional[GraphNode]:
        return self.load_graph().get_node(node_id)
