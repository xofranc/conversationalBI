"""Compatibility URLconf; the external composition root injects dependencies."""

from config.composition import build_user_urlpatterns

urlpatterns = build_user_urlpatterns()
