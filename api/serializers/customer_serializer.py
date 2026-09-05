from rest_framework import serializers


class CustomerSerializer(serializers.Serializer):
    _id = serializers.CharField()
    name = serializers.CharField()
    address = serializers.CharField()
    project = serializers.DictField()
    warranty = serializers.DictField()
    email = serializers.EmailField()
    phone = serializers.CharField()
    status = serializers.IntegerField()
