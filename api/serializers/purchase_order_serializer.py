from rest_framework import serializers
from api.models import PurchaseOrder
from api_sataiga.handlers.mongodb_handler import MongoDBHandler
from bson import ObjectId


class PurchaseOrderSerializer(serializers.ModelSerializer):
    id = serializers.SerializerMethodField(
        "get_id"
    )

    approved_date = serializers.SerializerMethodField(
        "get_approved_date"
    )

    supplier = serializers.SerializerMethodField(
        "get_supplier"
    )

    request_by_name = serializers.SerializerMethodField(
        "get_request_by_name"
    )

    approved_by_name = serializers.SerializerMethodField(
        "get_approved_by_name"
    )

    def __get_user(self, user_id):
        if user_id:
            with MongoDBHandler('users') as db:
                user = db.extract({'_id': ObjectId(user_id)})
                if user:
                    if 'lastname' in user[0] and user[0]['lastname'] != '':
                        return f"{user[0]['name']} {user[0]['lastname']}"
                    return user[0]['name']
        return ''

    def get_id(self, data):
        return str(data['_id'])

    def get_approved_date(self, data):
        if data['status'] > 1:
            return data['updated_at'].date().isoformat()
        return ''

    def get_supplier(self, data):
        with MongoDBHandler('suppliers') as db:
            supplier = db.extract({'_id': ObjectId(data['supplier_id'])})
            if supplier:
                supplier[0].pop('_id', None)
                return supplier[0]
            return None

    def get_request_by_name(self, data):
        return self.__get_user(data.get('request_by', None))

    def get_approved_by_name(self, data):
        return self.__get_user(data.get('approved_by', None))

    class Meta:
        model = PurchaseOrder
        fields = '__all__'
