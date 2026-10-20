"""Adaptador técnico para generación y limpieza de SQL del LLM."""

import re

from django.conf import settings

from .llm_client import LLMClient


class SQLAgent:
    def __init__(self):
        self.llm = LLMClient(
            model=settings.LLM_SQL_MODEL,
            temperature=0,
            max_tokens=220,
            stop=["\n\n", "PREGUNTA:", "Pregunta:", "Ejemplo:", "/*"],
        )

    def run(self, prompt: str) -> str:
        return self._clean(self.llm.complete(prompt))

    @staticmethod
    def _clean(raw: str) -> str:
        sql = raw.strip()
        fence = re.search(r"```(?:sql)?\s*(.*?)```", sql, re.DOTALL | re.IGNORECASE)
        if fence:
            sql = fence.group(1).strip()
        sql = re.sub(r"^(sql|consulta|respuesta|query)\s*:\s*", "", sql, flags=re.IGNORECASE)
        lines = []
        for line in sql.split("\n"):
            stripped = line.strip()
            if stripped.startswith("--"):
                continue
            if lines and re.match(r"(?i)^(explicaci[oó]n|nota|esto|la consulta|this|the query)\b", stripped):
                break
            lines.append(line)
        return "\n".join(lines).strip().rstrip(";").strip()
