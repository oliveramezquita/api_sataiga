from rest_framework import serializers
from api.models import Role
from api_sataiga.handlers.mongodb_handler import MongoDBHandler


class RoleSerializer(serializers.ModelSerializer):
    users = serializers.SerializerMethodField(
        "get_users"
    )

    def __set_full_name(self, user):
        full_name = user['name']
        if 'lastname' in user and user['lastname'] != '':
            full_name = f"{user['name']} {user['lastname']}"
        return full_name

    def get_users(self, data):
        with MongoDBHandler('users') as db:
            users = db.extract({'role_id': str(data['_id'])})

            return [{'_id': str(u['_id']), 'full_name': self.__set_full_name(u), 'email': u['email']} for u in users]

    class Meta:
        model = Role
        fields = '__all__'
