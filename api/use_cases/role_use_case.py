from urllib.parse import parse_qs
from api.constants import DEFAULT_PAGE_SIZE
from api.helpers.http_responses import ok, created, bad_request, ok_paginated
from api_sataiga.handlers.mongodb_handler import MongoDBHandler
from api.serializers.role_serializer import RoleSerializer
from api.helpers.validations import objectid_validation
from bson import ObjectId
from pymongo import errors
from django.core.paginator import Paginator


class RoleUseCase:
    def __init__(self, request=None, **kwargs):
        if request:
            params = parse_qs(request.META['QUERY_STRING'])
            self.page = params['page'][0] if 'page' in params else 1
            self.page_size = params['itemsPerPage'][0] \
                if 'itemsPerPage' in params else DEFAULT_PAGE_SIZE
        self.data = kwargs.get('data', None)
        self.id = kwargs.get('id', None)

    def save(self):
        with MongoDBHandler('roles') as db:
            required_fields = ['name', 'value', 'permissions']
            if all(i in self.data for i in required_fields):
                try:
                    db.create_unique_index('value')
                    db.insert(self.data)
                    return created('Rol creado correctamente.')
                except errors.DuplicateKeyError:
                    return bad_request('El valor del rol ya existe.')
            return bad_request('Algunos campos requeridos no han sido completados.')

    def get(self):
        with MongoDBHandler('roles') as db:
            roles = db.extract()
            paginator = Paginator(roles, per_page=self.page_size)
            page = paginator.get_page(self.page)
            return ok_paginated(
                paginator,
                page,
                RoleSerializer(page.object_list, many=True).data
            )

    def update(self):
        with MongoDBHandler('roles') as db:
            role = db.extract(
                {'_id': ObjectId(self.id)}) if objectid_validation(self.id) else None
            if role:
                db.update({'_id': ObjectId(self.id)}, self.data)
                return ok('Rol actualizado correctamente.')
            return bad_request('El rol no existe')
