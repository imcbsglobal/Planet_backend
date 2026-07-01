from rest_framework import serializers
from .models import Installation


class InstallationSerializer(serializers.ModelSerializer):
    feeder_name     = serializers.CharField(source="feeder.name", read_only=True, default="")
    attachment_url  = serializers.SerializerMethodField()
    attachment_name = serializers.SerializerMethodField()

    class Meta:
        model  = Installation
        fields = [
            "id", "key",
            "feeder", "feeder_name",
            "date",
            "attachment", "attachment_url", "attachment_name",
            "created_by",
            "created_at", "updated_at",
        ]
        read_only_fields = [
            "id", "feeder_name",
            "attachment_url", "attachment_name",
            "created_by", "created_at", "updated_at",
        ]

    def get_attachment_url(self, obj):
        if obj.attachment:
            request = self.context.get("request")
            if request:
                return request.build_absolute_uri(obj.attachment.url)
            return obj.attachment.url
        return None

    def get_attachment_name(self, obj):
        if obj.attachment:
            return obj.attachment.name.split("/")[-1]
        return None