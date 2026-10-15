"""Compatibility URLconf; the external composition root injects dependencies."""

from config.composition import build_dataset_urlpatterns

urlpatterns = build_dataset_urlpatterns()
