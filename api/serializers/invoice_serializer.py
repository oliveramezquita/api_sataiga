from rest_framework import serializers
from api.models import Invoice


class InvoiceSerializer(serializers.ModelSerializer):
    number = serializers.CharField(read_only=True, required=False)
    total = serializers.FloatField(read_only=True, required=False)
    project = serializers.CharField(read_only=True, required=False)
    supplier = serializers.DictField(read_only=True, required=False)

    class Meta:
        model = Invoice
        fields = '__all__'


class InvoiceUploadSerializer(serializers.Serializer):
    purchase_order_id = serializers.CharField(required=False)
    pdf_file = serializers.FileField(required=True)
    xml_file = serializers.FileField(required=True)

    def validate_pdf_file(self, value):
        if not value:
            raise serializers.ValidationError("El archivo PDF es obligatorio.")

        if not hasattr(value, 'name'):
            raise serializers.ValidationError(
                "El archivo PDF no fue enviado correctamente.")

        if not value.name.lower().endswith('.pdf'):
            raise serializers.ValidationError(
                "El archivo PDF no tiene una extensión válida.")

        return value

    def validate_xml_file(self, value):
        if not value:
            raise serializers.ValidationError("El archivo XML es obligatorio.")

        if not hasattr(value, 'name'):
            raise serializers.ValidationError(
                "El archivo XML no fue enviado correctamente.")

        if not value.name.lower().endswith('.xml'):
            raise serializers.ValidationError(
                "El archivo XML no tiene una extensión válida.")

        return value
