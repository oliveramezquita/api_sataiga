from urllib.parse import parse_qs
from api.constants import DEFAULT_PAGE_SIZE
from api_sataiga.handlers.mongodb_handler import MongoDBHandler
from api.helpers.http_responses import ok, ok_paginated
from django.core.paginator import Paginator
from api.serializers.special_project_serializer import SpecialProjectSerializer
from api.serializers.special_project_data_serializer import SpecialProjectDataSerializer


class SpecialProjectUseCase:
    def __init__(self, request=None, **kwargs):
        if request:
            params = parse_qs(request.META['QUERY_STRING'])
            self.page = params['page'][0] if 'page' in params else 1
            self.page_size = params['itemsPerPage'][0] \
                if 'itemsPerPage' in params else DEFAULT_PAGE_SIZE
            self.q = params['q'][0] if 'q' in params else None
        self.data = kwargs.get('data', None)
        self.client_id = kwargs.get('client_id', None)
        self.id = kwargs.get('id', None)

    def get_clients(self):
        with MongoDBHandler('clients') as db:
            filters = {'type': 'PE'}
            if self.q:
                filters['$or'] = [
                    {'name': {'$regex': self.q, '$options': 'i'}},
                    {'address': {'$regex': self.q, '$options': 'i'}},
                    {'email': {'$regex': self.q, '$options': 'i'}},
                ]
            clients = db.extract(filters, 'pe_id')
            return ok(SpecialProjectDataSerializer(clients, many=True).data)

    def get(self):
        with MongoDBHandler('special_projects') as db:
            filters = {'client_id': self.client_id}
            if self.q:
                filters['$or'] = [
                    {'name': {'$regex': self.q, '$options': 'i'}},
                    {'front': {'$regex': self.q, '$options': 'i'}},
                    {'location': {'$regex': self.q, '$options': 'i'}},
                ]
            special_projects = db.extract(filters)
            paginator = Paginator(special_projects, per_page=self.page_size)
            page = paginator.get_page(self.page)
            return ok_paginated(
                paginator,
                page,
                SpecialProjectSerializer(page.object_list, many=True).data
            )
