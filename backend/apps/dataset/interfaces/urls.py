from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import DatasetViewSet


def create_urlpatterns(use_cases, core_use_cases):
    configured_viewset = type(
        "ConfiguredDatasetViewSet",
        (DatasetViewSet,),
        {"use_cases": use_cases, "core_use_cases": core_use_cases},
    )
    router = DefaultRouter()
    router.register(r"", configured_viewset, basename="dataset")
    return [path("", include(router.urls))]
