from rest_framework import serializers
from api.models import Inbound
from api_sataiga.handlers.mongodb_handler import MongoDBHandler
from bson import ObjectId
from datetime import datetime


class InboundSerializer(serializers.ModelSerializer):
    purchase_order = serializers.SerializerMethodField(
        "get_purchase_order"
    )

    total_items = serializers.SerializerMethodField(
        "get_total_items"
    )

    supplier_name = serializers.SerializerMethodField(
        "get_supplier_name"
    )

    def get_supplier_name(self, data):
        with MongoDBHandler('suppliers') as db:
            supplier = db.extract({'_id': ObjectId(data['supplier_id'])})
            if supplier:
                return supplier[0]['name']
            return None

    def get_purchase_order(self, data):
        with MongoDBHandler('purchase_orders') as db:
            purchase_order = db.extract(
                {'_id': ObjectId(data['purchase_order_id'])})
            if purchase_order:
                return purchase_order[0]['number']
            return None

    def get_total_items(self, data):
        return len(data['items']) if 'items' in data else 0

    class Meta:
        model = Inbound
        fields = '__all__'
