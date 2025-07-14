from rest_framework import serializers
from api.models import Section


class SectionSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField(
        "get_name"
    )

    def get_name(self, data):
        name = data['parent']
        if 'level_1' in data and data['level_1'] != '':
            name = name + ' - ' + data['level_1']
        return name

    class Meta:
        model = Section
        fields = '__all__'
