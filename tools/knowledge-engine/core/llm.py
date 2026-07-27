from __future__ import annotations

import json
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class LLMResponse:
    content: str
    parsed: Optional[dict[str, Any]] = None
    model: str = ""
    usage: Optional[dict[str, int]] = None

    @property
    def is_valid_json(self) -> bool:
        return self.parsed is not None


class LLMProvider(ABC):
    @abstractmethod
    def complete(self, prompt: str, system_prompt: Optional[str] = None) -> LLMResponse:
        ...

    @abstractmethod
    def complete_json(self, prompt: str, system_prompt: Optional[str] = None) -> LLMResponse:
        ...


@dataclass
class LLMMessage:
    role: str
    content: str


@dataclass
class LLMConfig:
    provider: str = "openai"
    model: str = "gpt-4o"
    api_key: Optional[str] = None
    api_base: Optional[str] = None
    temperature: float = 0.1
    max_tokens: int = 4096
    timeout: int = 60


class OpenAIProvider(LLMProvider):
    def __init__(self, config: LLMConfig) -> None:
        self.config = config

    def complete(self, prompt: str, system_prompt: Optional[str] = None) -> LLMResponse:
        try:
            import openai
        except ImportError:
            return LLMResponse(content="", model=self.config.model)

        client_kwargs: dict[str, Any] = {"api_key": self.config.api_key}
        if self.config.api_base:
            client_kwargs["base_url"] = self.config.api_base

        client = openai.OpenAI(**client_kwargs)
        messages: list[dict[str, str]] = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        try:
            response = client.chat.completions.create(
                model=self.config.model,
                messages=messages,
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens,
                timeout=self.config.timeout,
            )
            content = response.choices[0].message.content or ""
            usage = {
                "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
                "completion_tokens": response.usage.completion_tokens if response.usage else 0,
                "total_tokens": response.usage.total_tokens if response.usage else 0,
            }
            return LLMResponse(content=content, model=self.config.model, usage=usage)
        except Exception as e:
            return LLMResponse(content=f"Error: {e}", model=self.config.model)

    def complete_json(self, prompt: str, system_prompt: Optional[str] = None) -> LLMResponse:
        sys = system_prompt or "You are a senior software architect. Always respond with valid JSON only."
        response = self.complete(prompt, sys)

        parsed = self._try_parse_json(response.content)
        if parsed:
            response.parsed = parsed
        return response

    def _try_parse_json(self, content: str) -> Optional[dict[str, Any]]:
        content = content.strip()
        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
            content = content.strip()
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            return None


class AnthropicProvider(LLMProvider):
    def __init__(self, config: LLMConfig) -> None:
        self.config = config

    def complete(self, prompt: str, system_prompt: Optional[str] = None) -> LLMResponse:
        try:
            import anthropic
        except ImportError:
            return LLMResponse(content="", model=self.config.model)

        client = anthropic.Anthropic(api_key=self.config.api_key)
        kwargs: dict[str, Any] = {
            "model": self.config.model,
            "max_tokens": self.config.max_tokens,
            "messages": [{"role": "user", "content": prompt}],
        }
        if system_prompt:
            kwargs["system"] = system_prompt

        try:
            response = client.messages.create(**kwargs)
            content = response.content[0].text if response.content else ""
            usage = {
                "input_tokens": response.usage.input_tokens if response.usage else 0,
                "output_tokens": response.usage.output_tokens if response.usage else 0,
            }
            return LLMResponse(content=content, model=self.config.model, usage=usage)
        except Exception as e:
            return LLMResponse(content=f"Error: {e}", model=self.config.model)

    def complete_json(self, prompt: str, system_prompt: Optional[str] = None) -> LLMResponse:
        sys = system_prompt or "You are a senior software architect. Always respond with valid JSON only."
        response = self.complete(prompt, sys)
        parsed = self._try_parse_json(response.content)
        if parsed:
            response.parsed = parsed
        return response

    def _try_parse_json(self, content: str) -> Optional[dict[str, Any]]:
        content = content.strip()
        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
            content = content.strip()
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            return None


class LLMFactory:
    @staticmethod
    def create(config: LLMConfig) -> LLMProvider:
        provider_map: dict[str, type[LLMProvider]] = {
            "openai": OpenAIProvider,
            "anthropic": AnthropicProvider,
            "claude": AnthropicProvider,
            "openrouter": OpenAIProvider,
            "gemini": OpenAIProvider,
            "kimi": OpenAIProvider,
            "opencode": OpenAIProvider,
        }
        provider_cls = provider_map.get(config.provider.lower(), OpenAIProvider)
        return provider_cls(config)
