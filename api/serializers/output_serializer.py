from rest_framework import serializers
from api.models import Output


class OutputSerializer(serializers.ModelSerializer):
    total_items = serializers.SerializerMethodField(
        "get_total_items"
    )

    def get_total_items(self, data):
        return len(data['items']) if 'items' in data else 0

    class Meta:
        model = Output
        fields = '__all__'
