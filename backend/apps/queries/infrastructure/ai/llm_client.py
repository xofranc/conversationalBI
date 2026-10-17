"""Cliente compatible con APIs de chat OpenAI configurado por Django."""

from django.conf import settings
from openai import BadRequestError, OpenAI


class LLMClient:
    def __init__(self, model: str, temperature: float, max_tokens: int, stop: list):
        self.client = OpenAI(
            api_key=settings.LLM_API_KEY,
            base_url=settings.LLM_BASE_URL,
            timeout=settings.LLM_TIMEOUT,
        )
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.stop = stop

    def complete(self, prompt: str) -> str:
        kwargs = {
            "model": self.model,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "stop": self.stop,
            "messages": [{"role": "user", "content": prompt}],
        }
        try:
            response = self.client.chat.completions.create(**kwargs)
        except BadRequestError as exc:
            if "temperature" not in str(exc):
                raise
            kwargs.pop("temperature")
            response = self.client.chat.completions.create(**kwargs)
        return response.choices[0].message.content or ""
