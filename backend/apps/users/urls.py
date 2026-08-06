from django.urls import path

from .views.profile import ProfileView

urlpatterns = [
    path("profile/", ProfileView.as_view(), name="profile"),
]
