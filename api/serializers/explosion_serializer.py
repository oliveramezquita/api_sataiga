from rest_framework import serializers
from api.models import Explosion
from api_sataiga.handlers.mongodb_handler import MongoDBHandler
from bson import ObjectId


class ExplosionSerializer(serializers.ModelSerializer):
    id = serializers.SerializerMethodField(
        "get_id"
    )

    home_production = serializers.SerializerMethodField(
        "get_home_production"
    )

    material = serializers.SerializerMethodField(
        "get_material"
    )

    def get_id(self, data):
        return str(data['_id'])

    def get_home_production(self, data):
        with MongoDBHandler('home_production') as db:
            home_production = db.extract(
                {'_id': ObjectId(data['home_production_id'])})
            if home_production:
                return f"{home_production[0]['front']} - {home_production[0]['od']}"
            return None

    def get_material(self, data):
        with MongoDBHandler('materials') as db:
            material = db.extract({'_id': ObjectId(data['material_id'])})
            if material:
                internal_code = ''
                if 'internal_code' in material[0] and material[0]['internal_code']:
                    internal_code = material[0]['internal_code']
                return {'name': material[0]['name'], 'measurement': material[0]['measurement'], 'internal_code': internal_code}
            return None

    class Meta:
        model = Explosion
        fields = '__all__'
