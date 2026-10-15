from django.urls import path

from .views import CleanupSessionView


def create_urlpatterns(use_cases):
    return [
        path(
            "session/",
            CleanupSessionView.as_view(use_cases=use_cases),
            name="cleanup-session",
        )
    ]
