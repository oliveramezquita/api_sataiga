from urllib.parse import parse_qs
from api.constants import DEFAULT_PAGE_SIZE
from api_sataiga.handlers.mongodb_handler import MongoDBHandler
from api.helpers.http_responses import created, bad_request, ok, ok_paginated, not_found
from django.core.paginator import Paginator
from api.serializers.client_serializer import ClientSerializer
from bson import ObjectId
from api.helpers.validations import objectid_validation


class ClientUseCase:
    def __init__(self, request=None, **kwargs):
        if request:
            params = parse_qs(request.META['QUERY_STRING'])
            self.page = params['page'][0] if 'page' in params else 1
            self.page_size = params['itemsPerPage'][0] \
                if 'itemsPerPage' in params else DEFAULT_PAGE_SIZE
            self.q = params['q'][0] if 'q' in params else None
        self.data = kwargs.get('data', None)
        self.id = kwargs.get('id', None)
        self.client_type = kwargs.get('client_type', None)

    def __create_consecutive(self):
        with MongoDBHandler('clients') as db:
            clients = db.extract({'type': 'PE'})
            if len(clients) == 0:
                return 1
            last = max(clients, key=lambda client: client['pe_id'])
            return int(last['pe_id']) + 1

    def save(self):
        with MongoDBHandler('clients') as db:
            required_fields = ['type', 'name']
            if all(i in self.data for i in required_fields):
                if self.data['type'] == 'PE':
                    self.data['pe_id'] = self.__create_consecutive()
                db.insert(self.data)
                return created('Cliente creado correctamente.')
            return bad_request('Algunos campos requeridos no han sido completados.')

    def get(self):
        with MongoDBHandler('clients') as db:
            filters = {'type': self.client_type}
            if self.q:
                filters['$or'] = [
                    {'name': {'$regex': self.q, '$options': 'i'}},
                    {'address': {'$regex': self.q, '$options': 'i'}},
                    {'email': {'$regex': self.q, '$options': 'i'}},
                ]
            order = 'pe_id' if self.client_type == 'PE' else None
            clients = db.extract(filters, order)
            paginator = Paginator(clients, per_page=self.page_size)
            page = paginator.get_page(self.page)
            return ok_paginated(
                paginator,
                page,
                ClientSerializer(page.object_list, many=True).data
            )

    def get_by_id(self):
        with MongoDBHandler('clients') as db:
            client = db.extract(
                {'_id': ObjectId(self.id)}) if objectid_validation(self.id) else None
            if client:
                return ok(ClientSerializer(client[0]).data)
            return not_found('El cliente no existe.')

    def update(self):
        with MongoDBHandler('clients') as db:
            client = db.extract(
                {'_id': ObjectId(self.id)}) if objectid_validation(self.id) else None
            if client:
                db.update({'_id': ObjectId(self.id)}, self.data)
                return ok('Cliente actualizado correctamente.')
            return bad_request('El cliente no existe.')

    def delete(self):
        with MongoDBHandler('clients') as db:
            client = db.extract(
                {'_id': ObjectId(self.id)}) if objectid_validation(self.id) else None
            if client:
                db.delete({'_id': ObjectId(self.id)})
                return ok('Cliente eliminado correctamente.')
            return bad_request('El cliente no existe.')
