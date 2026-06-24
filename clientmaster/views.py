from rest_framework import viewsets
from rest_framework.permissions import AllowAny
from .models import ClientMaster
from .serializers import ClientMasterSerializer


class ClientMasterViewSet(viewsets.ModelViewSet):
    queryset = ClientMaster.objects.select_related(
        "branch", "corporate", "district", "state", "country",
        "software", "business_nature", "service_pack",
    ).all()
    serializer_class   = ClientMasterSerializer
    permission_classes = [AllowAny]
