from rest_framework import serializers
from api.serializers.fields import SafeDecimalField
from api.models import Material
from api_sataiga.handlers.mongodb_handler import MongoDBHandler
from bson import ObjectId


class MaterialSerializer(serializers.ModelSerializer):
    minimum = SafeDecimalField(
        max_digits=10, decimal_places=2, required=False, allow_null=True)
    maximum = SafeDecimalField(
        max_digits=10, decimal_places=2, required=False, allow_null=True)
    unit_price = SafeDecimalField(
        max_digits=10, decimal_places=2, required=False, allow_null=True)
    inventory_price = SafeDecimalField(
        max_digits=10, decimal_places=2, required=False, allow_null=True)
    market_price = SafeDecimalField(
        max_digits=10, decimal_places=2, required=False, allow_null=True)
    price_difference = SafeDecimalField(
        max_digits=10, decimal_places=2, required=False, allow_null=True)

    id = serializers.SerializerMethodField(
        "get_id"
    )

    supplier = serializers.SerializerMethodField(
        "get_supplier"
    )

    inventory_id = serializers.SerializerMethodField(
        "get_inventory_id"
    )

    group = serializers.SerializerMethodField(
        "get_group"
    )

    json = serializers.SerializerMethodField(
        "get_json"
    )

    def get_id(self, data):
        return str(data['_id'])

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

    def get_group(self, data):
        with MongoDBHandler('catalogs') as db:
            equipment = db.extract({'name': 'Equipos y/o accesorios'})
            if equipment:
                if data['division'] in equipment[0]['values']:
                    return 'EQUIPMENT_GROUP'
            return 'MATERIALS_GROUP'

    def get_json(self, data):
        return {
            'id': str(data['_id']),
            'sku': data['sku'],
            'supplier_id': data['supplier_id'],
            'concept': data['concept'],
            'division': data['division'],
            'measurement': data['measurement'],
            'presentation': data.get('presentation')
        }

    class Meta:
        model = Material
        fields = '__all__'
