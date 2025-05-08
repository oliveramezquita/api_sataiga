from rest_framework import serializers
from api.models import Quantification


class QuantificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Quantification
        fields = '__all__'
