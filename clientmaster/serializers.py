from rest_framework import serializers
from .models import ClientMaster


class ClientMasterSerializer(serializers.ModelSerializer):
    branch_name          = serializers.CharField(source="branch.name",          read_only=True)
    corporate_name       = serializers.CharField(source="corporate.name",        read_only=True)
    district_name        = serializers.CharField(source="district.name",         read_only=True)
    state_name           = serializers.CharField(source="state.name",            read_only=True)
    country_name         = serializers.CharField(source="country.name",          read_only=True)
    software_name        = serializers.CharField(source="software.name",         read_only=True)
    business_nature_name = serializers.CharField(source="business_nature.name",  read_only=True)
    service_pack_name    = serializers.CharField(source="service_pack.name",     read_only=True)

    class Meta:
        model  = ClientMaster
        fields = [
            "id", "code", "status", "type",
            "branch", "branch_name",
            "corporate", "corporate_name",
            "suc_amount", "suc_end_date", "payment_class",
            "name", "address", "location", "place", "pin_code",
            "district", "district_name",
            "state", "state_name",
            "country", "country_name",
            "person_name", "reputed_person_name",
            "phone1", "phone2", "phone3",
            "reputed_person1", "reputed_person2", "email",
            "software", "software_name",
            "business_nature", "business_nature_name",
            "installation_date", "account_link",
            "licence_type", "no_of_seats",
            "service_pack", "service_pack_name",
            "renewal_date", "software_amount",
            "created_by", "created_at", "updated_at",
        ]
        read_only_fields = [
            "id", "created_at", "updated_at",
            "branch_name", "corporate_name", "district_name", "state_name",
            "country_name", "software_name", "business_nature_name", "service_pack_name",
        ]
