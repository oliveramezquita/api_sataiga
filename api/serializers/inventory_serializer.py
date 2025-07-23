from rest_framework import serializers
from api.models import Inventory
from api_sataiga.handlers.mongodb_handler import MongoDBHandler


class InventorySerializer(serializers.ModelSerializer):
    id = serializers.SerializerMethodField(
        "get_id"
    )

    last_inbound = serializers.SerializerMethodField(
        "get_last_inbound"
    )

    def get_id(self, data):
        return str(data['_id'])

    def get_last_inbound(self, data):
        with MongoDBHandler('inventory_quantity') as db:
            last_inbound = db.extract(
                {'inventory_id': str(data['_id'])}, 'created_at')
            if last_inbound:
                last_inbound[0].pop('_id', None)
                return last_inbound[0]
            return None

    class Meta:
        model = Inventory
        fields = '__all__'
