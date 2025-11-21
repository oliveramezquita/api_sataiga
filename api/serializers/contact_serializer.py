from rest_framework import serializers
from api.models import Contact
from bson import ObjectId
from api_sataiga.handlers.mongodb_handler import MongoDBHandler


class ContactSerializer(serializers.ModelSerializer):
    client = serializers.SerializerMethodField(
        "get_client"
    )

    def get_client(self, data) -> str:
        if not ObjectId.is_valid(data['client_id']):
            return {'name': '', 'type': None}
        try:
            with MongoDBHandler("clients") as db:
                client = db.extract({"_id": ObjectId(data['client_id'])})
                return {
                    'name': client[0].get("name", ""),
                    'type': client[0].get("type", None),
                }
        except Exception as e:
            # Logging opcional para debug
            return {'name': '', 'type': None}

    class Meta:
        model = Contact
        fields = '__all__'
