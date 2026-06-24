from rest_framework.routers import DefaultRouter
from .views import ClientMasterViewSet

router = DefaultRouter()
router.register(r"clientmaster", ClientMasterViewSet, basename="clientmaster")

urlpatterns = router.urls
