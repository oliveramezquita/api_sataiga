from rest_framework import serializers
from api.models import SpecialProject


class SpecialProjectSerializer(serializers.ModelSerializer):
    id = serializers.SerializerMethodField(
        "get_id"
    )

    def get_id(self, data):
        return str(data['_id'])

    class Meta:
        model = SpecialProject
        fields = '__all__'
