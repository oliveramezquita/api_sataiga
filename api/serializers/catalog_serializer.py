from rest_framework import serializers
from api.models import Catalog


class CatalogSerializer(serializers.ModelSerializer):
    id = serializers.SerializerMethodField(
        "get_id"
    )

    type = serializers.SerializerMethodField(
        "get_type"
    )

    def get_id(self, data):
        return str(data['_id'])

    def get_type(self, data):
        return str(type(data['values']).__name__)

    class Meta:
        model = Catalog
        fields = '__all__'
