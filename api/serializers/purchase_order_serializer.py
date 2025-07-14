from rest_framework import serializers
from api.models import PurchaseOrder


class PurchaseOrderSerializer(serializers.ModelSerializer):
    id = serializers.SerializerMethodField(
        "get_id"
    )

    approved_date = serializers.SerializerMethodField(
        "get_approved_date"
    )

    def get_id(self, data):
        return str(data['_id'])

    def get_approved_date(self, data):
        if data['status'] > 1:
            return data['updated_at'].date().isoformat()
        return ''

    class Meta:
        model = PurchaseOrder
        fields = '__all__'
