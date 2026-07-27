from __future__ import annotations

import html
from typing import Optional

from core.knowledge import KnowledgeObject


class HTMLRenderer:
    def render(self, ko: KnowledgeObject) -> str:
        lines: list[str] = [
            "<!DOCTYPE html>",
            '<html lang="en">',
            "<head>",
            '<meta charset="UTF-8">',
            '<meta name="viewport" content="width=device-width, initial-scale=1.0">',
            f"<title>{html.escape(ko.name)}</title>",
            "<style>",
            "body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 900px; margin: 0 auto; padding: 2rem; line-height: 1.6; color: #333; }",
            "h1, h2, h3 { color: #1a1a2e; }",
            "h2 { border-bottom: 2px solid #eee; padding-bottom: 0.5rem; margin-top: 2rem; }",
            ".meta { color: #666; font-size: 0.9rem; }",
            ".tag { display: inline-block; background: #e8e8e8; padding: 2px 8px; border-radius: 4px; font-size: 0.8rem; margin: 2px; }",
            ".section { margin: 1rem 0; }",
            "ul { padding-left: 1.5rem; }",
            "code { background: #f4f4f4; padding: 2px 6px; border-radius: 3px; font-size: 0.9rem; }",
            "footer { margin-top: 3rem; padding-top: 1rem; border-top: 1px solid #eee; color: #999; font-size: 0.8rem; }",
            "</style>",
            "</head>",
            "<body>",
        ]

        lines.append(f"<h1>{html.escape(ko.name)}</h1>")
        lines.append('<div class="meta">')
        if ko.type:
            lines.append(f"<span>Type: {html.escape(ko.type)}</span><br>")
        if ko.language:
            lines.append(f"<span>Language: {html.escape(ko.language)}</span><br>")
        if ko.source_file:
            lines.append(f"<span>Source: <code>{html.escape(ko.source_file)}</code></span><br>")
        for tag in ko.tags:
            lines.append(f'<span class="tag">{html.escape(tag)}</span>')
        lines.append("</div>")

        if ko.summary:
            lines.append('<div class="section">')
            lines.append(f"<p>{html.escape(ko.summary)}</p>")
            lines.append("</div>")

        if ko.purpose:
            lines.append("<h2>Purpose</h2>")
            lines.append(f"<p>{html.escape(ko.purpose)}</p>")

        if ko.responsibilities:
            lines.append("<h2>Responsibilities</h2>")
            lines.append("<ul>")
            for r in ko.responsibilities:
                lines.append(f"<li>{html.escape(r)}</li>")
            lines.append("</ul>")

        if ko.inputs:
            lines.append("<h2>Inputs</h2>")
            lines.append("<ul>")
            for inp in ko.inputs:
                lines.append(f"<li>{html.escape(inp)}</li>")
            lines.append("</ul>")

        if ko.outputs:
            lines.append("<h2>Outputs</h2>")
            lines.append("<ul>")
            for out in ko.outputs:
                lines.append(f"<li>{html.escape(out)}</li>")
            lines.append("</ul>")

        if ko.dependencies:
            lines.append("<h2>Dependencies</h2>")
            lines.append("<ul>")
            for dep in ko.dependencies:
                lines.append(f"<li>{html.escape(dep)}</li>")
            lines.append("</ul>")

        if ko.used_by:
            lines.append("<h2>Used By</h2>")
            lines.append("<ul>")
            for u in ko.used_by:
                lines.append(f"<li>{html.escape(u)}</li>")
            lines.append("</ul>")

        if ko.calls:
            lines.append("<h2>Calls</h2>")
            lines.append("<ul>")
            for c in ko.calls:
                lines.append(f"<li>{html.escape(c)}</li>")
            lines.append("</ul>")

        if ko.called_from:
            lines.append("<h2>Called From</h2>")
            lines.append("<ul>")
            for c in ko.called_from:
                lines.append(f"<li>{html.escape(c)}</li>")
            lines.append("</ul>")

        if ko.architecture_notes:
            lines.append("<h2>Architecture Notes</h2>")
            lines.append(f"<p>{html.escape(ko.architecture_notes)}</p>")

        if ko.improvements:
            lines.append("<h2>Suggested Improvements</h2>")
            lines.append("<ul>")
            for imp in ko.improvements:
                lines.append(f"<li>{html.escape(imp)}</li>")
            lines.append("</ul>")

        lines.append("<footer>")
        lines.append(f"<p>Last updated: {ko.last_updated}</p>")
        lines.append("</footer>")
        lines.append("</body>")
        lines.append("</html>")

        return "\n".join(lines)

    def render_to_file(self, ko: KnowledgeObject, output_path: str) -> None:
        content = self.render(ko)
        with open(output_path, "w") as f:
            f.write(content)
