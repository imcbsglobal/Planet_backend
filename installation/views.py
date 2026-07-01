from rest_framework import viewsets, status, parsers
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.db.models import Q

from .models import Installation
from .serializers import InstallationSerializer
from feeder.models import Feeder


def _get_username_from_request(request):
    """Extract username from custom Bearer token: 'Bearer local_{id}_{username}'"""
    auth_header = request.META.get("HTTP_AUTHORIZATION", "")
    if auth_header.startswith("Bearer local_"):
        remainder = auth_header[len("Bearer local_"):]   # "{id}_{username}"
        _, _, uname = remainder.partition("_")            # skip id, keep username
        if uname:
            return uname
    return ""


class InstallationViewSet(viewsets.ModelViewSet):
    queryset           = Installation.objects.select_related("feeder").all()
    serializer_class   = InstallationSerializer
    permission_classes = [AllowAny]
    parser_classes     = [parsers.MultiPartParser, parsers.FormParser, parsers.JSONParser]

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx["request"] = self.request
        return ctx

    def get_queryset(self):
        qs = super().get_queryset()
        q  = self.request.query_params.get("search", "").strip()
        if q:
            qs = qs.filter(
                Q(key__icontains=q) |
                Q(feeder__name__icontains=q) |
                Q(created_by__icontains=q)
            )
        return qs

    def perform_create(self, serializer):
        username = _get_username_from_request(self.request)
        instance = serializer.save(created_by=username or serializer.validated_data.get("created_by", ""))

        # Auto-update the linked feeder's status to "Installed"
        if instance.feeder_id:
            Feeder.objects.filter(pk=instance.feeder_id).update(status="Installed")

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def partial_update(self, request, *args, **kwargs):
        kwargs["partial"] = True
        instance   = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)