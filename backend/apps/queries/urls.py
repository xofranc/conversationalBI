from rest_framework.routers import DefaultRouter
from .views import QueryViewSet

router = DefaultRouter()
router.register(r'', QueryViewSet, basename='query')

urlpatterns = router.urls