"""Narrativa de resultados generada por LLM con fallback determinista."""

import logging

from django.conf import settings

from .llm_client import LLMClient
from .prompt_builder import PromptBuilder

logger = logging.getLogger(__name__)


class AnswerWriter:
    def __init__(self):
        self.llm = LLMClient(
            model=settings.LLM_ANSWER_MODEL,
            temperature=0.3,
            max_tokens=160,
            stop=["\n\n", "PREGUNTA:", "Pregunta:", "INSTRUCCIONES:"],
        )

    def write(self, question: str, sql: str, rows: list, row_count: int) -> str:
        if not rows:
            return ""
        try:
            answer = self.llm.complete(PromptBuilder.build_answer(question, sql, rows, row_count)).strip()
            if len(answer) >= 15:
                return " ".join(answer.split())
            logger.info("Narrativa demasiado corta (%d chars), usando respaldo", len(answer))
        except Exception as exc:
            logger.warning("AnswerWriter falló, usando respaldo: %s", exc)
        return self._fallback(rows, row_count)

    @staticmethod
    def _fallback(rows: list, row_count: int) -> str:
        first = rows[0]
        pairs = [f"{key} {AnswerWriter._fmt(value)}" for key, value in first.items() if value is not None]
        detail = ", ".join(pairs[:4])
        if row_count == 1:
            return f"El resultado es: {detail}."
        return f"Encontré {row_count} filas; la primera es {detail}."

    @staticmethod
    def _fmt(value) -> str:
        if isinstance(value, float):
            return f"{value:,.2f}".rstrip("0").rstrip(".")
        if isinstance(value, int):
            return f"{value:,}"
        return str(value)
