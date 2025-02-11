from rest_framework import serializers
from api.models.user import User


class UserSerializer(serializers.ModelSerializer):
    role_name = serializers.CharField(source='role.name')
    role_value = serializers.CharField(source='role.value')

    full_name = serializers.SerializerMethodField(
        "get_full_name"
    )

    def get_full_name(self, data):
        if 'lastname' in data and data['lastname'] != '':
            return f"{data['name']} {data['last_name']}"
        return data['name']

    class Meta:
        model = User
        fields = ('id', 'role', 'full_name', 'name', 'lastname', 'email', 'status',
                  'avatar', 'created_at', 'updated_at', 'role_name', 'role_value')
