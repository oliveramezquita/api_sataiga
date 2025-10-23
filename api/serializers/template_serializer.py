from rest_framework import serializers
from api.models import Template
from bson import ObjectId
from api_sataiga.handlers.mongodb_handler import MongoDBHandler


class TemplateSerializer(serializers.ModelSerializer):
    id = serializers.SerializerMethodField(
        "get_id"
    )

    client = serializers.SerializerMethodField(
        "get_client"
    )

    def get_id(self, data):
        return str(data['_id'])

    def get_client(self, data):
        if 'client_id' in data:
            with MongoDBHandler('clients') as db:
                client = db.extract({'_id': ObjectId(data['client_id'])})
                if client:
                    return {
                        '_id': str(client[0]['_id']),
                        'name': client[0]['name'],
                        'pe_id': client[0]['pe_id'],
                    }
            return None

    class Meta:
        model = Template
        fields = '__all__'
