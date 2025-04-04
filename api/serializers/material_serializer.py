from rest_framework import serializers
from api.models import Material
from api_sataiga.handlers.mongodb_handler import MongoDBHandler
from bson import ObjectId


class MaterialSerializer(serializers.ModelSerializer):
    supplier = serializers.SerializerMethodField(
        "get_supplier"
    )

    def get_supplier(self, data):
        with MongoDBHandler('suppliers') as db:
            client = db.extract({'_id': ObjectId(data['supplier_id'])})
            if client:
                return client[0]['name']
            return None

    class Meta:
        model = Material
        fields = '__all__'
