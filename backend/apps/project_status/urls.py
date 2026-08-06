from django.urls import path

from .views import project_status

urlpatterns = [
    path('', project_status, name='project-status'),
]
