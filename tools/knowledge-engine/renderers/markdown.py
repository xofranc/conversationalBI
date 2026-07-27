from __future__ import annotations

from typing import Optional

from core.knowledge import KnowledgeObject


class MarkdownRenderer:
    def render(self, ko: KnowledgeObject) -> str:
        lines: list[str] = []
        lines.append(f"# {ko.name}")
        lines.append("")

        if ko.type:
            lines.append(f"**Type:** {ko.type}")
        if ko.language:
            lines.append(f"**Language:** {ko.language}")
        if ko.summary:
            lines.append(f"**Summary:** {ko.summary}")
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

        if ko.inputs:
            lines.append("## Inputs")
            lines.append("")
            for inp in ko.inputs:
                lines.append(f"- {inp}")
            lines.append("")

        if ko.outputs:
            lines.append("## Outputs")
            lines.append("")
            for out in ko.outputs:
                lines.append(f"- {out}")
            lines.append("")

        if ko.dependencies:
            lines.append("## Dependencies")
            lines.append("")
            for dep in ko.dependencies:
                lines.append(f"- {dep}")
            lines.append("")

        if ko.used_by:
            lines.append("## Used By")
            lines.append("")
            for u in ko.used_by:
                lines.append(f"- {u}")
            lines.append("")

        if ko.calls:
            lines.append("## Calls")
            lines.append("")
            for c in ko.calls:
                lines.append(f"- {c}")
            lines.append("")

        if ko.called_from:
            lines.append("## Called From")
            lines.append("")
            for c in ko.called_from:
                lines.append(f"- {c}")
            lines.append("")

        if ko.architecture_notes:
            lines.append("## Architecture Notes")
            lines.append("")
            lines.append(ko.architecture_notes)
            lines.append("")

        if ko.improvements:
            lines.append("## Suggested Improvements")
            lines.append("")
            for imp in ko.improvements:
                lines.append(f"- {imp}")
            lines.append("")

        if ko.source_file:
            lines.append("## Source")
            lines.append("")
            lines.append(f"`{ko.source_file}`")
            lines.append("")

        if ko.tags:
            lines.append(f"**Tags:** {', '.join(ko.tags)}")

        lines.append("")
        lines.append("---")
        lines.append(f"*Last updated: {ko.last_updated}*")

        return "\n".join(lines)

    def render_index(self, knowledge_objects: list[KnowledgeObject], title: str = "Knowledge Base") -> str:
        lines: list[str] = []
        lines.append(f"# {title}")
        lines.append("")
        lines.append(f"Total entries: {len(knowledge_objects)}")
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
                summary = ko.summary[:100] + "..." if len(ko.summary) > 100 else ko.summary
                lines.append(f"- [{ko.name}]({ko.id}.md)")
                if summary:
                    lines.append(f"  - {summary}")
            lines.append("")

        return "\n".join(lines)

    def render_to_file(self, ko: KnowledgeObject, output_path: str) -> None:
        import os
        content = self.render(ko)
        with open(output_path, "w") as f:
            f.write(content)
