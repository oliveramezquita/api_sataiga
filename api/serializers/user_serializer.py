from rest_framework import serializers
from api.models.user import User


class UserSerializer(serializers.ModelSerializer):
    role_name = serializers.CharField(source='role.name')
    role_value = serializers.CharField(source='role.value')

    class Meta:
        model = User
        fields = ('id', 'role', 'name', 'lastname', 'email', 'status',
                  'avatar', 'created_at', 'updated_at', 'role_name', 'role_value')
