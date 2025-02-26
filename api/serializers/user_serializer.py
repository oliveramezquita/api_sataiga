from rest_framework import serializers
from api.models import User
from api_sataiga.handlers.mongodb_handler import MongoDBHandler
from api.constants import USER_STATUS
from bson import ObjectId


class UserSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField(
        "get_full_name"
    )
    role = serializers.SerializerMethodField(
        "get_role"
    )
    status_label = serializers.SerializerMethodField(
        "get_user_status"
    )

    def get_full_name(self, data):
        if 'lastname' in data and data['lastname'] != '':
            return f"{data['name']} {data['lastname']}"
        return data['name']

    def get_role(self, data):
        with MongoDBHandler('roles') as db:
            role = db.extract({'_id': ObjectId(data['role_id'])})
        return {'name': role[0]['name'], 'value': role[0]['value']}

    def get_user_status(self, data):
        return next((v for k, v in USER_STATUS if k == data['status']), None)

    class Meta:
        model = User
        fields = '__all__'
