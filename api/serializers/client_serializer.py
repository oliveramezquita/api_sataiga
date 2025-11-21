from rest_framework import serializers
from api.models import Client


class ClientSerializer(serializers.ModelSerializer):
    id = serializers.SerializerMethodField(
        "get_id"
    )

    def get_id(self, data):
        return str(data['_id'])

    class Meta:
        model = Client
        fields = '__all__'
