from rest_framework import serializers
from api.models import Inventory
from api_sataiga.handlers.mongodb_handler import MongoDBHandler
from api.use_cases.output_use_case import OutputUseCase
from api.use_cases.inbound_use_case import InboundUseCase
from bson import ObjectId


class InventorySerializer(serializers.ModelSerializer):
    id = serializers.SerializerMethodField(
        "get_id"
    )

    last_inbound = serializers.SerializerMethodField(
        "get_last_inbound"
    )

    last_output = serializers.SerializerMethodField(
        "get_last_output"
    )

    def __get_extra_data(self, output):
        if 'client_id' in output and output['client_id']:
            with MongoDBHandler('clients') as db:
                client = db.extract({'_id': ObjectId(output['client_id'])})
                if client:
                    output['client_name'] = client[0]['name']
                    return output
                return None

    def get_id(self, data):
        return str(data['_id'])

    def get_last_inbound(self, data):
        inbounds = InboundUseCase.get_by_external(
            data['material']['id'], {'status': 1})
        if len(inbounds) > 0:
            return inbounds[0]
        return None

    def get_last_output(self, data):
        outputs = OutputUseCase.get_by_external(
            data['material']['id'], {'status': {'$in': [1, 3]}})
        if len(outputs) > 0:
            return self.__get_extra_data(outputs[0])
        return None

    class Meta:
        model = Inventory
        fields = '__all__'
