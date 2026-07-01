from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import InstallationViewSet

router = DefaultRouter()
router.register(r"installations", InstallationViewSet, basename="installation")

urlpatterns = [
    path("", include(router.urls)),
]
