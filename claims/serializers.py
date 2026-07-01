from rest_framework import serializers

from .models import Claim


class ClaimSerializer(serializers.ModelSerializer):
    # Read-only convenience fields for the list page
    user = serializers.SerializerMethodField()
    date = serializers.SerializerMethodField()
    purpose = serializers.CharField(source="description", read_only=True)
    category = serializers.CharField(source="expense_type", read_only=True)
    has_receipt = serializers.SerializerMethodField()

    class Meta:
        model = Claim
        fields = [
            "id",
            "company",
            "department",
            "department_name",
            "client",
            "client_name",
            "expense_type",
            "amount",
            "description",
            "receipt",
            "status",
            "created_by",
            "created_by_name",
            "created_at",
            "updated_at",
            # convenience/read-only aliases matching the frontend table
            "user",
            "date",
            "purpose",
            "category",
            "has_receipt",
        ]
        read_only_fields = ["id", "created_by", "created_by_name", "created_at", "updated_at"]

    def get_user(self, obj):
        # Prefer the denormalised name (set at create time from the token)
        if obj.created_by_name:
            return obj.created_by_name
        # Fallback: resolve from the FK if it exists
        if obj.created_by_id:
            cb = obj.created_by
            full = getattr(cb, "get_full_name", lambda: "")()
            return full.strip() or getattr(cb, "email", None) or cb.username
        return None

    def get_date(self, obj):
        return obj.created_at.strftime("%d %b %Y") if obj.created_at else None

    def get_has_receipt(self, obj):
        return bool(obj.receipt)

    def validate_amount(self, value):
        if value is None or value <= 0:
            raise serializers.ValidationError("Amount must be greater than 0.")
        return value

    def validate_description(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("Description is required.")
        return value


class ClaimStatusUpdateSerializer(serializers.ModelSerializer):
    """Lightweight serializer used by the inline status dropdown on the list page."""

    class Meta:
        model = Claim
        fields = ["id", "status"]