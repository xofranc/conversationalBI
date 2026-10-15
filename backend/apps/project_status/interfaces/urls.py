from django.urls import path

from .views import ProjectStatusView


def create_urlpatterns(use_cases):
    return [
        path(
            "",
            ProjectStatusView.as_view(use_cases=use_cases),
            name="project-status",
        )
    ]
