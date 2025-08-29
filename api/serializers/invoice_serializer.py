from rest_framework import serializers


class InvoiceUploadSerializer(serializers.Serializer):
    pdf_file = serializers.FileField()
    xml_file = serializers.FileField()
