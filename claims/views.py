from rest_framework import viewsets, status as http_status, filters
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

from .models import Claim
from .serializers import ClaimSerializer, ClaimStatusUpdateSerializer


class ClaimViewSet(viewsets.ModelViewSet):
    """
    /api/claims/                -> list, create
    /api/claims/<id>/           -> retrieve, update, partial_update, destroy
    /api/claims/<id>/status/    -> PATCH inline status update (used by the list page dropdown)
    """

    queryset = Claim.objects.select_related("created_by").all()
    serializer_class = ClaimSerializer
    permission_classes = [AllowAny]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["status", "expense_type", "department", "company"]
    search_fields = ["client_name", "description", "created_by__email", "created_by__username"]
    ordering_fields = ["created_at", "amount"]
    ordering = ["-created_at"]

    def get_queryset(self):
        qs = super().get_queryset()
        # With the local token auth, request.user is always anonymous.
        # Role-based scoping is done via the token's embedded username instead.
        username = self._username_from_request(self.request)
        if not username:
            return qs  # unauthenticated — return all (AllowAny is set)

        # Try to load the UserProfile for role checking
        try:
            from usermanagement.models import UserProfile
            profile = UserProfile.objects.get(username__iexact=username)
            role = profile.role
        except Exception:
            role = "User"

        if role in ("Super Admin", "Admin"):
            return qs
        # Regular users see only their own claims
        return qs.filter(created_by_name__iexact=username)

    def _username_from_request(self, request):
        """
        Extract the display name from the local token (format: local_{id}_{username})
        or fall back to whatever is stored in localStorage via the X-Username header.
        """
        auth = request.META.get("HTTP_AUTHORIZATION", "")
        if auth.startswith("Bearer local_"):
            # token format: local_<id>_<username>
            parts = auth[len("Bearer local_"):].split("_", 1)
            if len(parts) == 2:
                return parts[1]  # username portion
        # Fallback: try a custom header the frontend can send
        return request.META.get("HTTP_X_USERNAME", "")

    def perform_create(self, serializer):
        name = self._username_from_request(self.request)
        serializer.save(created_by_name=name)

    @action(detail=True, methods=["patch"], url_path="status")
    def update_status(self, request, pk=None):
        claim = self.get_object()
        serializer = ClaimStatusUpdateSerializer(claim, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(ClaimSerializer(claim).data, status=http_status.HTTP_200_OK)
