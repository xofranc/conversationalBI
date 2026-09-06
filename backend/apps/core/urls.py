# apps/core/urls.py
from django.urls import path
from .views import cleanup_session

urlpatterns = [
    path('session/', cleanup_session, name='cleanup-session'),
]
