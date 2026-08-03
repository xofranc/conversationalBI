import re

from django.conf import settings

from .llm_client import LLMClient


class SQLAgent:

    def __init__(self):
        self.llm = LLMClient(
            model       = settings.LLM_SQL_MODEL,
            temperature = 0,    # determinista — crítico para SQL consistente
            max_tokens  = 220,  # el SQL cabe de sobra; corta divagaciones del modelo
            stop        = ['\n\n', 'PREGUNTA:', 'Pregunta:', 'Ejemplo:', '/*'],
        )

    def run(self, prompt: str) -> str:
        response = self.llm.complete(prompt)
        return self._clean(response)

    @staticmethod
    def _clean(raw: str) -> str:
        """Extrae el SQL de la respuesta cruda del LLM."""
        sql = raw.strip()

        # Bloque markdown ```sql ... ``` → se queda el contenido
        fence = re.search(r'```(?:sql)?\s*(.*?)```', sql, re.DOTALL | re.IGNORECASE)
        if fence:
            sql = fence.group(1).strip()

        # Prefijos típicos: "SQL:", "Consulta:", "Respuesta:"
        sql = re.sub(r'^(sql|consulta|respuesta|query)\s*:\s*', '', sql, flags=re.IGNORECASE)

        # Corta cualquier cola explicativa tras la primera sentencia completa
        lines = []
        for line in sql.split('\n'):
            stripped = line.strip()
            if stripped.startswith('--'):          # comentarios del modelo
                continue
            if lines and re.match(r'(?i)^(explicaci[oó]n|nota|esto|la consulta|this|the query)\b', stripped):
                break
            lines.append(line)
        sql = '\n'.join(lines).strip().rstrip(';').strip()

        return sql
