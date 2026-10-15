"""
URL configuration for conversationalBI project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.http import JsonResponse
from django.urls import include, path

from .composition import build_interface_urlpatterns


def health(_request):
    """Health check para Render (healthCheckPath) y el ping anti cold-start."""
    return JsonResponse({'status': 'ok'})


interface_urlpatterns = build_interface_urlpatterns()

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/health/', health),
    path('api/v1/project-status/', include(interface_urlpatterns['project_status'])),
    path('api/v1/users/', include(interface_urlpatterns['users'])),
    path('api/v1/dataset/', include(interface_urlpatterns['dataset'])),
    path('api/v1/queries/', include(interface_urlpatterns['queries'])),
    path('api/v1/core/', include(interface_urlpatterns['core'])),
]
