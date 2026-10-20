from django.urls import path

from .views import ProfileView


def create_urlpatterns(use_cases):
    return [
        path(
            "profile/",
            ProfileView.as_view(use_cases=use_cases),
            name="profile",
        )
    ]
