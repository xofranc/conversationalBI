import logging

from django.conf import settings

from .llm_client import LLMClient
from .prompt_builder import PromptBuilder

logger = logging.getLogger(__name__)


class AnswerWriter:
    """
    Redacta la respuesta en lenguaje natural a partir de los resultados.
    Segundo paso de la conversación: el SQL trae las filas, el writer
    las convierte en una respuesta completa en español.
    Si el LLM falla, hay un resumen determinista de respaldo.
    """

    def __init__(self):
        self.llm = LLMClient(
            model       = settings.LLM_ANSWER_MODEL,
            temperature = 0.3,  # un punto de soltura para prosa natural
            max_tokens  = 160,  # 2-4 frases bastan
            stop        = ['\n\n', 'PREGUNTA:', 'Pregunta:', 'INSTRUCCIONES:'],
        )

    def write(self, question: str, sql: str, rows: list, row_count: int) -> str:
        if not rows:
            return ''
        try:
            prompt = PromptBuilder.build_answer(question, sql, rows, row_count)
            answer = self.llm.complete(prompt).strip()
            # Descarta respuestas vacías o sospechosamente cortas
            if len(answer) >= 15:
                return ' '.join(answer.split())
            logger.info('Narrativa demasiado corta (%d chars), usando respaldo', len(answer))
        except Exception as e:
            logger.warning('AnswerWriter falló, usando respaldo: %s', e)
        return AnswerWriter._fallback(rows, row_count)

    @staticmethod
    def _fallback(rows: list, row_count: int) -> str:
        """Resumen sin LLM: encabezado del resultado en prosa plana."""
        primera = rows[0]
        pares = [f'{k} {AnswerWriter._fmt(v)}' for k, v in primera.items() if v is not None]
        detalle = ', '.join(pares[:4])
        if row_count == 1:
            return f'El resultado es: {detalle}.'
        return f'Encontré {row_count} filas; la primera es {detalle}.'

    @staticmethod
    def _fmt(val) -> str:
        if isinstance(val, float):
            return f'{val:,.2f}'.rstrip('0').rstrip('.')
        if isinstance(val, int):
            return f'{val:,}'
        return str(val)
