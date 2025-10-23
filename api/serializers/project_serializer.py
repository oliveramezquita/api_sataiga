from rest_framework import serializers
from api.models import Project
from bson import ObjectId
from api_sataiga.handlers.mongodb_handler import MongoDBHandler


class ProjectSerializer(serializers.ModelSerializer):
    id = serializers.SerializerMethodField(
        "get_id"
    )

    client = serializers.SerializerMethodField(
        "get_client"
    )

    status_label = serializers.SerializerMethodField(
        "get_status_label"
    )

    def get_id(self, data):
        return str(data['_id'])

    def get_client(self, data):
        with MongoDBHandler('clients') as db:
            client = db.extract({'_id': ObjectId(data['client_id'])})
            if client:
                return {
                    '_id': str(client[0]['_id']),
                    'name': client[0]['name'],
                    'pe_id': client[0]['pe_id'],
                }
            return None

    def get_status_label(self, data):
        STATUS = ['Diseño', 'Cotización',
                  'Producción', 'Instalación', 'Entregado']
        return STATUS[data['status']]

    class Meta:
        model = Project
        fields = '__all__'
