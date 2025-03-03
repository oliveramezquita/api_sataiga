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
        if 'level_2' in data and data['level_2'] != '':
            name = data['level_1'] + ' - ' + data['level_2']
        return name

    class Meta:
        model = Section
        fields = '__all__'
