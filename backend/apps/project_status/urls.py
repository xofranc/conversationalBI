"""Compatibility URLconf; the external composition root injects dependencies."""

from config.composition import build_project_status_urlpatterns

urlpatterns = build_project_status_urlpatterns()
