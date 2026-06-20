from rest_framework import serializers
from django.contrib.auth.hashers import make_password
from .models import UserProfile


class UserProfileSerializer(serializers.ModelSerializer):
    password      = serializers.CharField(write_only=True, required=False, allow_blank=True)
    branch_name   = serializers.CharField(source="branch.name", read_only=True)
    profile_photo = serializers.ImageField(required=False, allow_null=True)

    class Meta:
        model  = UserProfile
        fields = [
            "id", "username", "address", "phone",
            "branch", "branch_name",
            "role", "status",
            "password",
            "profile_photo",
            "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at", "branch_name"]

    def create(self, validated_data):
        raw_password = validated_data.pop("password", "")
        if raw_password:
            validated_data["password"] = make_password(raw_password)
        return super().create(validated_data)

    def update(self, instance, validated_data):
        raw_password = validated_data.pop("password", "")
        if raw_password:
            validated_data["password"] = make_password(raw_password)
        return super().update(instance, validated_data)