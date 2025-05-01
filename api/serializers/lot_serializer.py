from rest_framework import serializers
from api.models import Lot


class LotSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lot
        fields = '__all__'
