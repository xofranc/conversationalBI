import re

from langchain_ollama import OllamaLLM
from django.conf import settings


class SQLAgent:

    def __init__(self):
        self.llm = OllamaLLM(
            model         = getattr(settings, 'OLLAMA_MODEL', 'qwen2.5-coder:7b'),
            base_url      = getattr(settings, 'OLLAMA_HOST', 'http://localhost:11434'),
            temperature   = 0,   # determinista — crítico para SQL consistente
            seed          = 42,  # reproducibilidad (misma pregunta → mismo SQL)
            num_predict   = 220, # el SQL cabe de sobra; corta divagaciones del modelo
            stop          = ['\n\n', 'PREGUNTA:', 'Pregunta:', 'Ejemplo:', '/*'],
            client_kwargs = {'timeout': getattr(settings, 'OLLAMA_TIMEOUT', 60)},
        )

    def run(self, prompt: str) -> str:
        response = self.llm.invoke(prompt)
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
