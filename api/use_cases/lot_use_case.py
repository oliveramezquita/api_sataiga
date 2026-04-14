from bson import ObjectId
from collections import Counter
from api_sataiga.handlers.mongodb_handler import MongoDBHandler
from api.helpers.http_responses import ok, not_found
from api.serializers.lot_serializer import LotSerializer
from api.decorators.service_method import service_method
from api.helpers.validations import objectid_validation
from api.use_cases.explosion_use_case import ExplosionUseCase
from api.services.lot_service import LotService


class LotUseCase:
    def __init__(self, request=None, **kwargs):
        if request:
            self.request = request
        self.data = kwargs.get('data', None)
        self.id = kwargs.get('id', None)
        self.home_production_id = kwargs.get('home_production_id', None)
        self.service = LotService()

    @service_method()
    def save(self):
        return self.service.create(self.home_production_id, self.data)

    @service_method()
    def get(self):
        return self.service.get(self.home_production_id)

    @service_method()
    def update(self):
        return self.service.update(self.home_production_id, self.data)

    @service_method()
    def delete(self):
        return self.service.delete(self.id)

    @service_method()
    def upload(self):
        return self.service.upload(self.home_production_id,
                                   self.data, self.request.FILES['file'])
