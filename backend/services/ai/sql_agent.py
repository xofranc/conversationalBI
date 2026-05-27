from langchain_ollama import OllamaLLM
from django.conf import settings


class SQLAgent:

    def __init__(self):
        self.llm = OllamaLLM(
            model       = getattr(settings, 'OLLAMA_MODEL', 'qwen2.5-coder:7b'),
            base_url    = getattr(settings, 'OLLAMA_HOST', 'http://localhost:11434'),
            temperature = 0,   # determinista — crítico para SQL consistente
        )

    def run(self, prompt: str) -> str:
        response = self.llm.invoke(prompt)
        return self._clean(response)

    @staticmethod
    def _clean(raw: str) -> str:
        """Elimina bloques markdown que el LLM suele agregar."""
        sql = raw.strip()
        if '```' in sql:
            lines = sql.split('\n')
            sql   = '\n'.join(
                line for line in lines
                if not line.strip().startswith('```')
            )
        return sql.strip()