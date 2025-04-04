from rest_framework import serializers
from api.models import Catalog


class CatalogSerializer(serializers.ModelSerializer):
    class Meta:
        model = Catalog
        fields = '__all__'
