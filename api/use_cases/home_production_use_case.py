from bson import ObjectId
from api.helpers.get_query_params import get_query_params
from api_sataiga.handlers.mongodb_handler import MongoDBHandler
from api.decorators.service_method import service_method
from api.helpers.validations import objectid_validation
from api.helpers.http_responses import ok_paginated, ok, not_found, bad_request
from api.serializers.home_production_serializer import HomeProductionSerializer
from api.services.home_production_service import HomeProductionService
from api.utils.pagination_utils import DummyPaginator, DummyPage


class HomeProdcutionUseCase:
    def __init__(self, request=None, **kwargs):
        params = get_query_params(request)
        self.q = params["q"]
        self.page = params["page"]
        self.page_size = params["page_size"]
        self.sort_by = params["sort_by"]
        self.order_by = params["order_by"]
        self.data = kwargs.get('data', None)
        self.id = kwargs.get('id', None)
        self.service = HomeProductionService()

    @service_method(success_status="created")
    def save(self):
        """Crea una nueva OD."""
        self.service.create(self.data)
        return 'OD creada correctamente.'

    def get(self):
        try:
            filters = {}
            if self.q:
                q = str(self.q)
                filters['$or'] = [
                    {'front': {'$regex': q, '$options': 'i'}},
                    {'od': {'$regex': q, '$options': 'i'}},
                ]

            result = self.service.get_paginated(
                filters, self.page, self.page_size, self.sort_by, self.order_by
            )

            dummy_paginator = DummyPaginator(
                result["count"], result["total_pages"])
            dummy_page = DummyPage(
                result["current_page"], dummy_paginator, result["results"]
            )

            return ok_paginated(dummy_paginator, dummy_page, result["results"])
        except Exception as e:
            return bad_request(f"Error al obtener OD's: {e}")

    @service_method()
    def get_by_id(self):
        return self.service.get_by_id(self.id)

    @service_method()
    def update(self):
        return self.service.update(self.id, self.data)

    @service_method()
    def delete(self):
        return self.service.delete(self.id)
