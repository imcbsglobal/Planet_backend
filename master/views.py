from rest_framework import viewsets
from rest_framework.permissions import AllowAny
from .models import Branch, Software, BusinessNature, District, State, Country, SP, Corporate, Module
from .serializers import (
    BranchSerializer, SoftwareSerializer, BusinessNatureSerializer,
    DistrictSerializer, StateSerializer, CountrySerializer, SPSerializer,
    CorporateSerializer, ModuleSerializer,
)


class BranchViewSet(viewsets.ModelViewSet):
    queryset = Branch.objects.all()
    serializer_class = BranchSerializer
    permission_classes = [AllowAny]


class SoftwareViewSet(viewsets.ModelViewSet):
    queryset = Software.objects.all()
    serializer_class = SoftwareSerializer
    permission_classes = [AllowAny]


class BusinessNatureViewSet(viewsets.ModelViewSet):
    queryset = BusinessNature.objects.all()
    serializer_class = BusinessNatureSerializer
    permission_classes = [AllowAny]


class DistrictViewSet(viewsets.ModelViewSet):
    queryset = District.objects.all()
    serializer_class = DistrictSerializer
    permission_classes = [AllowAny]


class StateViewSet(viewsets.ModelViewSet):
    queryset = State.objects.all()
    serializer_class = StateSerializer
    permission_classes = [AllowAny]


class CountryViewSet(viewsets.ModelViewSet):
    queryset = Country.objects.all()
    serializer_class = CountrySerializer
    permission_classes = [AllowAny]


class SPViewSet(viewsets.ModelViewSet):
    queryset = SP.objects.all()
    serializer_class = SPSerializer
    permission_classes = [AllowAny]


class CorporateViewSet(viewsets.ModelViewSet):
    queryset = Corporate.objects.all()
    serializer_class = CorporateSerializer
    permission_classes = [AllowAny]


class ModuleViewSet(viewsets.ModelViewSet):
    queryset = Module.objects.all()
    serializer_class = ModuleSerializer
    permission_classes = [AllowAny]