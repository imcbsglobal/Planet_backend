from rest_framework import serializers
from .models import Collection


class CollectionSerializer(serializers.ModelSerializer):
    proof_required     = serializers.BooleanField(read_only=True)
    payment_proof_url  = serializers.SerializerMethodField()
    payment_proof_name = serializers.SerializerMethodField()

    class Meta:
        model = Collection
        fields = [
            'id',
            'company',
            'department',
            'client_name',
            'collection_type',
            'amount',
            'paid_for',
            'payment_proof',
            'payment_proof_url',
            'payment_proof_name',
            'notes',
            'status',
            'created_by',
            'created_by_name',
            'created_at',
            'updated_at',
            'proof_required',
        ]
        read_only_fields = ['id', 'created_by', 'created_at', 'updated_at']

    def get_payment_proof_url(self, obj):
        if not obj.payment_proof:
            return None
        request = self.context.get('request')
        if request:
            return request.build_absolute_uri(obj.payment_proof.url)
        return obj.payment_proof.url

    def get_payment_proof_name(self, obj):
        if obj.payment_proof:
            return obj.payment_proof.name.split('/')[-1]
        return None