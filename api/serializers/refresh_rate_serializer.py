from rest_framework import serializers
from api.models import RefreshRate


class RefreshRateSerializer(serializers.ModelSerializer):
    class Meta:
        model = RefreshRate
        fields = '__all__'
