from rest_framework import serializers
from api.models import PurchaseOrder
from datetime import datetime


class PurchaseOrderSerializer(serializers.ModelSerializer):
    approved_date = serializers.SerializerMethodField(
        "get_approved_date"
    )

    def get_approved_date(self, data):
        if data['status'] > 1:
            return data['updated_at'].date().isoformat()
        return ''

    class Meta:
        model = PurchaseOrder
        fields = '__all__'
