from rest_framework.routers import DefaultRouter

from .views import QueryViewSet


def create_urlpatterns(use_cases, core_use_cases):
    configured_viewset = type(
        "ConfiguredQueryViewSet",
        (QueryViewSet,),
        {"use_cases": use_cases, "core_use_cases": core_use_cases},
    )
    router = DefaultRouter()
    router.register(r"", configured_viewset, basename="query")
    return router.urls
