from urllib.parse import parse_qs
from api.constants import DEFAULT_PAGE_SIZE
from api_sataiga.handlers.mongodb_handler import MongoDBHandler
from api.helpers.http_responses import created, bad_request, ok, ok_paginated, not_found
from django.core.paginator import Paginator
from api.serializers.supplier_serializer import SupplierSerializer
from bson import ObjectId
from api.helpers.validations import objectid_validation


class SupplierUseCase:
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
        with MongoDBHandler('suppliers') as db:
            required_fields = ['name']
            if all(i in self.data for i in required_fields):
                db.insert(self.data)
                return created('Proveedor creado correctamente.')
            return bad_request('Algunos campos requeridos no han sido completados.')

    def get(self):
        with MongoDBHandler('suppliers') as db:
            filters = {}
            if self.q:
                filters['$or'] = [
                    {'name': {'$regex': self.q, '$options': 'i'}},
                    {'address': {'$regex': self.q, '$options': 'i'}},
                    {'email': {'$regex': self.q, '$options': 'i'}},
                ]
            suppliers = db.extract(filters)
            paginator = Paginator(suppliers, per_page=self.page_size)
            page = paginator.get_page(self.page)
            return ok_paginated(
                paginator,
                page,
                SupplierSerializer(page.object_list, many=True).data
            )

    def get_by_id(self):
        with MongoDBHandler('suppliers') as db:
            supplier = db.extract(
                {'_id': ObjectId(self.id)}) if objectid_validation(self.id) else None
            if supplier:
                return ok(SupplierSerializer(supplier[0]).data)
            return not_found('El proveedor no existe.')

    def update(self):
        with MongoDBHandler('suppliers') as db:
            supplier = db.extract(
                {'_id': ObjectId(self.id)}) if objectid_validation(self.id) else None
            if supplier:
                db.update({'_id': ObjectId(self.id)}, self.data)
                return ok('Proveedor actualizado correctamente.')
            return not_found('El proveedor no existe.')

    def delete(self):
        with MongoDBHandler('suppliers') as db:
            supplier = db.extract(
                {'_id': ObjectId(self.id)}) if objectid_validation(self.id) else None
            if supplier:
                db.delete({'_id': ObjectId(self.id)})
                return ok('Proveedor eliminado correctamente.')
            return not_found('El proveedor no existe.')
