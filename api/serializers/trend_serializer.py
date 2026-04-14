from rest_framework import serializers
from api.models import Trend
from bson import ObjectId
from api_sataiga.handlers.mongodb_handler import MongoDBHandler


class TrendSerializer(serializers.ModelSerializer):
    client_name = serializers.SerializerMethodField(
        "get_client_name"
    )

    def get_client_name(self, data) -> str:
        if not ObjectId.is_valid(data['client_id']):
            return ''

        with MongoDBHandler("clients") as db:
            client = db.extract({"_id": ObjectId(data['client_id'])})
            if client:
                return client[0].get("name", "")
        return ''

    class Meta:
        model = Trend
        fields = '__all__'
