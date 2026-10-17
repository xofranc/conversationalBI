"""Compatibility URLconf; the external composition root injects dependencies."""

from config.composition import build_core_urlpatterns

urlpatterns = build_core_urlpatterns()
