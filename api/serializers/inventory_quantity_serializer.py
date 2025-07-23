from rest_framework import serializers
from api.models import InventoryQuantity


class InventoryQuantitySerializer(serializers.ModelSerializer):
    class Meta:
        model = InventoryQuantity
        fields = '__all__'
