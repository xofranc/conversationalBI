import logging

from langchain_ollama import OllamaLLM
from django.conf import settings

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
        self.llm = OllamaLLM(
            model         = getattr(settings, 'OLLAMA_MODEL', 'qwen2.5-coder:7b'),
            base_url      = getattr(settings, 'OLLAMA_HOST', 'http://localhost:11434'),
            temperature   = 0.3,  # un punto de soltura para prosa natural
            num_predict   = 160,  # 2-4 frases bastan; en CPU cada token cuesta
            stop          = ['\n\n', 'PREGUNTA:', 'Pregunta:', 'INSTRUCCIONES:'],
            client_kwargs = {'timeout': getattr(settings, 'OLLAMA_TIMEOUT', 60)},
        )

    def write(self, question: str, sql: str, rows: list, row_count: int) -> str:
        if not rows:
            return ''
        try:
            prompt = PromptBuilder.build_answer(question, sql, rows, row_count)
            answer = self.llm.invoke(prompt).strip()
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
