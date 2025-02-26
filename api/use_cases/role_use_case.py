import logging
from api.helpers.http_responses import ok, created, bad_request, error
from api_sataiga.handlers.mongodb_handler import MongoDBHandler
from api.serializers.role_serializer import RoleSerializer
from api.helpers.validations import objectid_validation
from bson import ObjectId
from pymongo import errors

log = logging.getLogger(__name__)


class RoleUseCase:
    def __init__(self, **kwargs):
        self.data = kwargs.get('data', None)
        self.id = kwargs.get('id', None)

    def save(self):
        with MongoDBHandler('roles') as db:
            required_fields = ['name', 'value']
            if all(i in self.data for i in required_fields):
                try:
                    db.create_unique_index('value')
                    db.insert(self.data)
                    return created('Rol creado correctamente.')
                except errors.DuplicateKeyError:
                    return bad_request('El valor del rol ya existe.')
                except Exception as e:
                    log.error(e.args[0])
                    return error(e.args[0])
            return bad_request('Algunos campos requeridos no han sido completados.')

    def get(self):
        with MongoDBHandler('roles') as db:
            roles = db.extract()
            return ok(RoleSerializer(roles, many=True).data)

    def update(self):
        with MongoDBHandler('roles') as db:
            role = db.extract(
                {'_id': ObjectId(self.id)}) if objectid_validation(self.id) else None
            if role:
                try:
                    db.update({'_id': ObjectId(self.id)}, self.data)
                    return ok('Rol actualizado correctamente.')
                except Exception as e:
                    log.error(e.args[0])
                    return error(e.args[0])
            return bad_request('El rol no existe')
