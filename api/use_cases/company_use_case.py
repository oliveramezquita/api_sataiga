from api_sataiga.handlers.mongodb_handler import MongoDBHandler
from api.helpers.http_responses import created, bad_request, ok_paginated, ok, not_found
from django.core.paginator import Paginator
from api.serializers.company_serializer import CompanySerializer
from urllib.parse import parse_qs
from api.constants import DEFAULT_PAGE_SIZE
from bson import ObjectId
from api.helpers.validations import objectid_validation


class CompanyUseCase:
    def __init__(self, request=None, **kwargs):
        if request:
            params = parse_qs(request.META['QUERY_STRING'])
            self.page = params['page'][0] if 'page' in params else 1
            self.page_size = params['itemsPerPage'][0] \
                if 'itemsPerPage' in params else DEFAULT_PAGE_SIZE
            self.q = params['q'][0] if 'q' in params else None
        self.data = kwargs.get('data', None)
        self.id = kwargs.get('id', None)

    def save(self):
        with MongoDBHandler('companies') as db:
            required_fields = ['name', 'rfc']
            if all(i in self.data for i in required_fields):
                db.insert(self.data)
                return created('Compañía creada correctamente.')
            return bad_request('Algunos campos requeridos no han sido completados.')

    def get(self):
        with MongoDBHandler('companies') as db:
            filters = {}
            if self.q:
                filters['$or'] = [
                    {'name': {'$regex': self.q, '$options': 'i'}},
                    {'rfc': {'$regex': self.q, '$options': 'i'}},
                    {'address': {'$regex': self.q, '$options': 'i'}},
                    {'city': {'$regex': self.q, '$options': 'i'}},
                    {'state': {'$regex': self.q, '$options': 'i'}},
                    {'email': {'$regex': self.q, '$options': 'i'}},
                ]
            companies = db.extract(filters)
            paginator = Paginator(companies, per_page=self.page_size)
            page = paginator.get_page(self.page)
            return ok_paginated(
                paginator,
                page,
                CompanySerializer(page.object_list, many=True).data
            )

    def update(self):
        with MongoDBHandler('companies') as db:
            company = db.extract(
                {'_id': ObjectId(self.id)}) if objectid_validation(self.id) else None
            if company:
                db.update({'_id': ObjectId(self.id)}, self.data)
                return ok('Compañía actualizada correctamente.')
            return not_found('La compañía no existe.')

    def delete(self):
        with MongoDBHandler('companies') as db:
            company = db.extract(
                {'_id': ObjectId(self.id)}) if objectid_validation(self.id) else None
            if company:
                db.delete({'_id': ObjectId(self.id)})
                return ok('Compañía eliminada correctamente.')
            return not_found('La compañía no existe.')
