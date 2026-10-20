from django.urls import include, path
from rest_framework.permissions import BasePermission
from rest_framework.routers import DefaultRouter

from .views import DatasetViewSet


def create_urlpatterns(use_cases, *, identity_provider, permission_class):
    if not callable(identity_provider):
        raise TypeError("identity_provider must be callable")
    if not isinstance(permission_class, type) or not issubclass(
        permission_class, BasePermission
    ):
        raise TypeError("permission_class must subclass BasePermission")

    configured_viewset = type(
        "ConfiguredDatasetViewSet",
        (DatasetViewSet,),
        {
            "use_cases": use_cases,
            # staticmethod evita que Python lo convierta en método bound y le
            # pase self además de request.
            "identity_provider": staticmethod(identity_provider),
            "permission_classes": [permission_class],
        },
    )
    router = DefaultRouter()
    router.register(r"", configured_viewset, basename="dataset")
    return [path("", include(router.urls))]
