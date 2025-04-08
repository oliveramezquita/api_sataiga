from rest_framework import serializers


class ExcelUploadSerializer(serializers.Serializer):
    file = serializers.FileField()
