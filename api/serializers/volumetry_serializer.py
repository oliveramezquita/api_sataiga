from rest_framework import serializers
from api.models import Volumetry
from api_sataiga.handlers.mongodb_handler import MongoDBHandler
from bson import ObjectId


class VolumetrySerializer(serializers.ModelSerializer):
    id = serializers.SerializerMethodField(
        "get_id"
    )

    material = serializers.SerializerMethodField(
        "get_material"
    )

    def get_id(self, data):
        return str(data['_id'])

    def get_material(self, data):
        with MongoDBHandler('materials') as db:
            material = db.extract({'_id': ObjectId(data['material_id'])})
            if material:
                sku = ''
                if 'sku' in material[0] and material[0]['sku']:
                    sku = material[0]['sku']
                return {
                    'concept': material[0]['concept'],
                    'measurement': material[0]['measurement'],
                    'sku': sku,
                    'division': material[0]['division'],
                }
            return None

    class Meta:
        model = Volumetry
        fields = '__all__'
