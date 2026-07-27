from pathlib import Path


class MarkdownRenderer:

    def __init__(self, vault_path: Path):
        self.vault = vault_path

    def render_node(self, node, category, related):

        folder = self.vault / category
        folder.mkdir(parents=True, exist_ok=True)

        label = node.get("label", "Unknown").replace("/", "_")

        file = folder / f"{label}.md"

        markdown = []

        markdown.append(f"# {label}\n\n")

        markdown.append("## Información\n\n")

        markdown.append(f"- Archivo: `{node.get('source_file', '')}`\n")
        markdown.append(f"- Tipo: `{node.get('file_type', '')}`\n")
        markdown.append(f"- Comunidad: `{node.get('community_name', '')}`\n\n")

        markdown.append("## Relacionado con\n\n")

        if related:
            for rel in related:
                markdown.append(f"- [[{rel}]]\n")
        else:
            markdown.append("- Sin relaciones detectadas.\n")

        file.write_text("".join(markdown), encoding="utf-8")