from pathlib import Path

from parser import GraphParser
from classifier import NodeClassifier
from renderer import MarkdownRenderer

ROOT = Path(__file__).resolve().parents[2]

GRAPH = ROOT / "graphify-out" / "graph.json"
VAULT = ROOT / "vault"

parser = GraphParser(GRAPH)
renderer = MarkdownRenderer(VAULT)

nodes = parser.get_nodes()
relationships = parser.build_relationships()
created = 0

for index, node in enumerate(nodes):

    if NodeClassifier.should_ignore(node):
        continue

    category = NodeClassifier.classify(node)

    related_indexes = relationships.get(index, [])

    related_labels = []

    for rel in related_indexes:

        if rel >= len(nodes):
            continue

        label = nodes[rel].get("label")

        if label:
            related_labels.append(label.replace("/", "_"))

    renderer.render_node(
        node,
        category,
        related_labels
    )

    created += 1

print(f"\nNotas generadas: {created}")