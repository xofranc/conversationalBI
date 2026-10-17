from rest_framework.permissions import BasePermission
from rest_framework.routers import DefaultRouter

from .views import QueryViewSet


def create_urlpatterns(use_cases, *, identity_provider, permission_class):
    if not callable(identity_provider):
        raise TypeError("identity_provider must be callable")
    if not isinstance(permission_class, type) or not issubclass(
        permission_class, BasePermission
    ):
        raise TypeError("permission_class must subclass BasePermission")

    configured_viewset = type(
        "ConfiguredQueryViewSet",
        (QueryViewSet,),
        {
            "use_cases": use_cases,
            "identity_provider": identity_provider,
            "permission_classes": [permission_class],
        },
    )
    router = DefaultRouter()
    router.register(r"", configured_viewset, basename="query")
    return router.urls
