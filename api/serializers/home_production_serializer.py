from rest_framework import serializers
from api.models import HomeProduction
from bson import ObjectId
from api_sataiga.handlers.mongodb_handler import MongoDBHandler


class HomeProductionSerializer(serializers.ModelSerializer):
    client = serializers.SerializerMethodField(
        "get_client"
    )

    def get_client(self, data):
        with MongoDBHandler('clients') as db:
            client = db.extract({'_id': ObjectId(data['client_id'])})
            if client:
                return client[0]['name']
            return None

    class Meta:
        model = HomeProduction
        fields = '__all__'
