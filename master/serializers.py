from rest_framework import serializers
from .models import Branch, Software, BusinessNature, District, State, Country, SP, Corporate


class BranchSerializer(serializers.ModelSerializer):
    class Meta:
        model = Branch
        fields = ["id", "code", "name", "created_at", "updated_at"]


class SoftwareSerializer(serializers.ModelSerializer):
    class Meta:
        model = Software
        fields = ["id", "code", "name", "created_at", "updated_at"]


class BusinessNatureSerializer(serializers.ModelSerializer):
    class Meta:
        model = BusinessNature
        fields = ["id", "code", "name", "created_at", "updated_at"]


class DistrictSerializer(serializers.ModelSerializer):
    class Meta:
        model = District
        fields = ["id", "code", "name", "created_at", "updated_at"]


class StateSerializer(serializers.ModelSerializer):
    class Meta:
        model = State
        fields = ["id", "code", "name", "created_at", "updated_at"]


class CountrySerializer(serializers.ModelSerializer):
    class Meta:
        model = Country
        fields = ["id", "code", "name", "created_at", "updated_at"]


class SPSerializer(serializers.ModelSerializer):
    class Meta:
        model = SP
        fields = ["id", "code", "name", "created_at", "updated_at"]


class CorporateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Corporate
        fields = ["id", "code", "name", "created_at", "updated_at"]