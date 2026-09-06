# apps/queries/services/pipeline/tests/test_base.py
import pytest
from ..base import Middleware


class ConcreteMiddleware(Middleware):
    def process(self, context):
        context['processed'] = True
        return context


def test_middleware_is_callable():
    middleware = ConcreteMiddleware()
    context = {'test': True}
    result = middleware(context)
    assert result['processed'] is True


def test_middleware_process_method():
    middleware = ConcreteMiddleware()
    context = {'test': True}
    result = middleware.process(context)
    assert result['processed'] is True
    assert result['test'] is True
