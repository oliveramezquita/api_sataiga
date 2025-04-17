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
                return {'name': material[0]['name'], 'measurement': material[0]['measurement']}
            return None

    class Meta:
        model = Volumetry
        fields = '__all__'
