"""Compatibility URLconf; the external composition root injects dependencies."""

from config.composition import build_query_urlpatterns

urlpatterns = build_query_urlpatterns()
