import json
from pathlib import Path


class GraphParser:
    def __init__(self, graph_path: Path):
        self.graph_path = graph_path

    def load(self):
        """Carga el graph.json"""
        with open(self.graph_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def get_nodes(self):
        """Devuelve todos los nodos"""
        graph = self.load()
        return graph.get("nodes", [])

    def get_links(self):
        """Devuelve todas las relaciones"""
        graph = self.load()
        return graph.get("links", [])

    def build_relationships(self):

        graph = self.load()

        links = graph.get("links", [])

        relations = {}

        for link in links:

            source = link.get("source")
            target = link.get("target")

            if source is None or target is None:
                continue

            relations.setdefault(source, []).append(target)
            relations.setdefault(target, []).append(source)

        return relations
