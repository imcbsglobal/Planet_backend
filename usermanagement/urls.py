from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import UserProfileViewSet, local_login

router = DefaultRouter()
router.register(r"users", UserProfileViewSet, basename="user")

urlpatterns = [
    path("", include(router.urls)),
    path("login/", local_login),   # → /api/usermanagement/login/
]