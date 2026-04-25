from rest_framework.routers import DefaultRouter
from django.urls import include, path
from .views import DatasetViewSet

router = DefaultRouter()
router.register(r'', DatasetViewSet, basename='dataset')  # r'' evita el prefijo doble

urlpatterns = [
    path('', include(router.urls)),
]