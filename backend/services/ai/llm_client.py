from openai import OpenAI
from django.conf import settings


class LLMClient:
    """
    Cliente agnóstico de proveedor: cualquier endpoint OpenAI-compatible
    (OpenCode Go, Groq, OpenRouter, Ollama). Cambiar de proveedor son
    env vars (LLM_BASE_URL / LLM_API_KEY / LLM_*_MODEL), no código.
    """

    def __init__(self, model: str, temperature: float, max_tokens: int, stop: list):
        self.client = OpenAI(
            api_key  = settings.LLM_API_KEY,
            base_url = settings.LLM_BASE_URL,
            timeout  = settings.LLM_TIMEOUT,
        )
        self.model       = model
        self.temperature = temperature
        self.max_tokens  = max_tokens
        self.stop        = stop

    def complete(self, prompt: str) -> str:
        resp = self.client.chat.completions.create(
            model       = self.model,
            temperature = self.temperature,
            max_tokens  = self.max_tokens,
            stop        = self.stop,
            messages    = [{'role': 'user', 'content': prompt}],
        )
        return resp.choices[0].message.content or ''
