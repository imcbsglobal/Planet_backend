from rest_framework import serializers
from .models import Feeder


class FeederSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Feeder
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]

    # Map camelCase keys from the React form → snake_case model fields
    # so the frontend can POST with its own field names directly.
    def to_internal_value(self, data):
        camel_to_snake = {
            "contactPerson":  "contact_person",
            "reputedName":    "reputed_name",
            "reputedPhone":   "reputed_phone",
            "businessNature": "business_nature",
            "noOfSystem":     "no_of_system",
            "pinCode":        "pin_code",
            "installDate":    "install_date",
            "softwareAmount": "software_amount",
            "totalCost":      "total_cost",
            "createdBy":      "created_by",
            "admStatus":      "adm_status",
        }
        # Fields where an empty string should become None
        nullable_fields = {"no_of_system", "install_date", "software_amount", "total_cost"}

        mapped = {}
        for k, v in data.items():
            snake_key = camel_to_snake.get(k, k)
            # Normalise empty strings → None for nullable numeric/date fields
            if snake_key in nullable_fields and v == "":
                v = None
            # Reformat date from DD-MM-YYYY → YYYY-MM-DD if needed
            if snake_key == "install_date" and v and isinstance(v, str) and v.count("-") == 2:
                parts = v.split("-")
                if len(parts[0]) == 2 and len(parts[2]) == 4:   # DD-MM-YYYY
                    v = f"{parts[2]}-{parts[1]}-{parts[0]}"
            mapped[snake_key] = v
        return super().to_internal_value(mapped)

    def to_representation(self, instance):
        """Return camelCase keys so the React list/form can consume the API directly."""
        rep = super().to_representation(instance)
        snake_to_camel = {
            "contact_person":  "contactPerson",
            "reputed_name":    "reputedName",
            "reputed_phone":   "reputedPhone",
            "business_nature": "businessNature",
            "no_of_system":    "noOfSystem",
            "pin_code":        "pinCode",
            "install_date":    "installDate",
            "software_amount": "softwareAmount",
            "total_cost":      "totalCost",
            "created_by":      "createdBy",
            "adm_status":      "admStatus",
            "created_at":      "createdAt",
            "updated_at":      "updatedAt",
        }
        return {snake_to_camel.get(k, k): v for k, v in rep.items()}