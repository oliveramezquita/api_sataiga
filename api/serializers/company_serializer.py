from rest_framework import serializers
from api.models import Company


class CompanySerializer(serializers.ModelSerializer):
    id = serializers.SerializerMethodField(
        "get_id"
    )

    def get_id(self, data):
        return str(data['_id'])

    class Meta:
        model = Company
        fields = '__all__'
