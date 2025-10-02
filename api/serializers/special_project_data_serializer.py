import uuid
from rest_framework import serializers
from api.models import Client


class SpecialProjectDataSerializer(serializers.ModelSerializer):
    total_projects = serializers.SerializerMethodField(
        "get_total_projects"
    )

    project_data = serializers.SerializerMethodField(
        "get_project_data"
    )

    def get_total_projects(self, data):
        return 0

    def get_project_data(self, data):
        return [
            {
                'id': uuid.uuid4().hex,
                'color': 'secondary',
                'icon': 'tabler-color-picker',
                'title': 'Diseño',
                'count': 0,
            },
            {
                'id': uuid.uuid4().hex,
                'color': 'info',
                'icon': 'tabler-cash-register',
                'title': 'Cotización',
                'count': 0,
            },
            {
                'id': uuid.uuid4().hex,
                'color': 'success',
                'icon': 'tabler-building-factory-2',
                'title': 'Producción',
                'count': 0,
            },
            {
                'id': uuid.uuid4().hex,
                'color': 'warning',
                'icon': 'tabler-package-export',
                'title': 'Instalación',
                'count': 0,
            }
        ]

    class Meta:
        model = Client
        fields = '__all__'
