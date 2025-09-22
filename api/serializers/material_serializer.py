from rest_framework import serializers
from api.models import Material
from api_sataiga.handlers.mongodb_handler import MongoDBHandler
from bson import ObjectId


class MaterialSerializer(serializers.ModelSerializer):
    supplier = serializers.SerializerMethodField(
        "get_supplier"
    )

    inventory_id = serializers.SerializerMethodField(
        "get_inventory_id"
    )

    def get_supplier(self, data):
        with MongoDBHandler('suppliers') as db:
            supplier = db.extract({'_id': ObjectId(data['supplier_id'])})
            if supplier:
                return supplier[0]['name']
            return None

    def get_inventory_id(self, data):
        with MongoDBHandler('inventory') as db:
            inventory = db.extract({'material.id': str(data['_id'])})
            if inventory:
                return str(inventory[0]['_id'])
            return None

    class Meta:
        model = Material
        fields = '__all__'
