from api_sataiga.handlers.mongodb_handler import MongoDBHandler
from bson import ObjectId
from api.helpers.validations import objectid_validation
from api.helpers.http_responses import created, bad_request, ok_paginated, ok, not_found
from django.core.paginator import Paginator
from api.serializers.home_production_serializer import HomeProductionSerializer
from urllib.parse import parse_qs
from api.constants import DEFAULT_PAGE_SIZE


class HomeProdcutionUseCase:
    def __init__(self, request=None, **kwargs):
        if request:
            params = parse_qs(request.META['QUERY_STRING'])
            self.page = params['page'][0] if 'page' in params else 1
            self.page_size = params['itemsPerPage'][0] \
                if 'itemsPerPage' in params else DEFAULT_PAGE_SIZE
        self.data = kwargs.get('data', None)
        self.id = kwargs.get('id', None)

    def __client_validation(self, db, client_id):
        client = MongoDBHandler.find(db, 'clients', {'_id': ObjectId(
            client_id), 'type': 'VS'}) if objectid_validation(client_id) else None
        if client:
            return client[0]
        return False

    def save(self):
        with MongoDBHandler('home_production') as db:
            required_fields = ['client_id', 'front', 'od']
            if all(i in self.data for i in required_fields):
                if self.__client_validation(db, self.data['client_id']):
                    db.insert({
                        **self.data,
                        'lots': {},
                        'progress': 0,
                        'status': 0})
                    return created('OD creada correctamente.')
                return bad_request('El cliente seleccionado no existe.')
            return bad_request('Algunos campos requeridos no han sido completados.')

    def get(self):
        with MongoDBHandler('home_production') as db:
            home_production = db.extract()
            paginator = Paginator(home_production, per_page=self.page_size)
            page = paginator.get_page(self.page)
            return ok_paginated(
                paginator,
                page,
                HomeProductionSerializer(page.object_list, many=True).data
            )

    def get_by_id(self):
        with MongoDBHandler('home_production') as db:
            home_production = db.extract(
                {'_id': ObjectId(self.id)}) if objectid_validation(self.id) else None
            if home_production:
                return ok(HomeProductionSerializer(home_production[0]).data)
            return not_found('La OD no existe.')

    def update(self):
        with MongoDBHandler('home_production') as db:
            home_production = db.extract(
                {'_id': ObjectId(self.id)}) if objectid_validation(self.id) else None
            if home_production:
                db.update({'_id': ObjectId(self.id)}, self.data)
                return ok('OD actualizada correctamente.')
            return not_found('La OD noexiste.')

    def delete(self):
        with MongoDBHandler('home_production') as db:
            home_production = db.extract(
                {'_id': ObjectId(self.id)}) if objectid_validation(self.id) else None
            if home_production:
                db.delete({'_id': ObjectId(self.id)})
                return ok('OD eliminada correctamente.')
            return not_found('La OD noexiste.')
