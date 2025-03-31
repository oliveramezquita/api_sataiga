from rest_framework import serializers
from api.models import Prototype


class PrototypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Prototype
        fields = '__all__'
