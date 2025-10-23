from rest_framework import serializers


class ProjectStatusSerializer(serializers.Serializer):
    id = serializers.CharField()
    color = serializers.CharField()
    icon = serializers.CharField()
    title = serializers.CharField()
    count = serializers.IntegerField()


class ProjectDataSerializer(serializers.Serializer):
    _id = serializers.CharField()
    name = serializers.CharField()
    type = serializers.CharField()
    pe_id = serializers.IntegerField()
    total_projects = serializers.IntegerField()
    project_data = ProjectStatusSerializer(many=True)
