from rest_framework import serializers
from api.models import Concept
from bson import ObjectId
from api_sataiga.handlers.mongodb_handler import MongoDBHandler


class ConceptSerializer(serializers.ModelSerializer):
    project = serializers.SerializerMethodField(
        "get_project"
    )

    def get_project(self, data):
        STATUS = ['Diseño', 'Cotización',
                  'Producción', 'Instalación', 'Entregado']
        with MongoDBHandler('projects') as db:
            client = db.extract({'_id': ObjectId(data['project_id'])})
            if client:
                return {
                    '_id': str(client[0]['_id']),
                    'client_id': client[0]['client_id'],
                    'name': client[0]['name'],
                    'status': client[0]['status'],
                    'status_label': STATUS[client[0]['status']],
                }
            return None

    class Meta:
        model = Concept
        fields = '__all__'
