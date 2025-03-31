from rest_framework import serializers
from api.models import Volumetry


class VolumetrySerializer(serializers.ModelSerializer):
    class Meta:
        model = Volumetry
        fields = '__all__'
