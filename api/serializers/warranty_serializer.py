from rest_framework import serializers
from after_sales.models import Warranty


class WarrantySerializer(serializers.ModelSerializer):
    class Meta:
        model = Warranty
        fields = '__all__'
