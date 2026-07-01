from rest_framework import viewsets, filters
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.contrib.auth.hashers import check_password
from django_filters.rest_framework import DjangoFilterBackend
from .models import UserProfile
from .serializers import UserProfileSerializer


class UserProfileViewSet(viewsets.ModelViewSet):
    queryset           = UserProfile.objects.select_related("branch").all()
    serializer_class   = UserProfileSerializer
    permission_classes = [AllowAny]
    filter_backends    = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields   = ["role", "status", "branch"]
    search_fields      = ["username", "phone", "address"]
    ordering_fields    = ["username", "created_at"]
    ordering           = ["-created_at"]

    def partial_update(self, request, *args, **kwargs):
        kwargs["partial"] = True
        return self.update(request, *args, **kwargs)


# ─── Local Login ──────────────────────────────────────────────────────────────
@api_view(["POST"])
@permission_classes([AllowAny])
def local_login(request):
    username = request.data.get("username", "").strip()
    password = request.data.get("password", "")

    if not username or not password:
        return Response({"detail": "Username and password required."}, status=400)

    try:
        user = UserProfile.objects.select_related("branch").get(username__iexact=username)
    except UserProfile.DoesNotExist:
        return Response({"detail": "Invalid credentials."}, status=401)

    if user.status != "Active":
        return Response(
            {"detail": "Account is inactive. Contact your administrator."},
            status=403,
        )

    if not check_password(password, user.password):
        return Response({"detail": "Invalid credentials."}, status=401)

    return Response({
        "token":    f"local_{user.id}_{user.username}",
        "role":     user.role,
        "username": user.username,
        "branch":   user.branch.name if user.branch else "",
    })