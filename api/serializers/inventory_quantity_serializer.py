from rest_framework import serializers
from api.models import InventoryQuantity


class InventoryQuantitySerializer(serializers.ModelSerializer):
    output = serializers.SerializerMethodField(
        "get_output"
    )

    def get_output(self, data):
        return 0

    class Meta:
        model = InventoryQuantity
        fields = '__all__'
