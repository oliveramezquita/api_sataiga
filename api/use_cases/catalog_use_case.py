from api_sataiga.handlers.mongodb_handler import MongoDBHandler
from api.helpers.http_responses import created, bad_request, ok, not_found
from api.serializers.catalog_serializer import CatalogSerializer
from bson import ObjectId
from api.helpers.validations import objectid_validation
from urllib.parse import parse_qs


class CatalogUseCase:
    def __init__(self, request=None, data=None, id=None):
        if request:
            params = parse_qs(request.META['QUERY_STRING'])
            self.name = params['name'][0] if 'name' in params else None
        self.data = data
        self.id = id

    def save(self):
        with MongoDBHandler('catalogs') as db:
            required_fields = ['name', 'values']
            if all(i in self.data for i in required_fields):
                db.insert(self.data)
                return created('Catálogo creado correctamente.')
            return bad_request('Algunos campos requeridos no han sido completados.')

    def get(self):
        with MongoDBHandler('catalogs') as db:
            if self.name:
                catalog = db.extract({'name': self.name})
                if catalog:
                    return ok(CatalogSerializer(catalog[0]).data)
                return not_found(f'El catálogo {self.name} no existe.')
            catalogs = db.extract()
            if catalogs:
                return ok(CatalogSerializer(catalogs, many=True).data)
            return not_found('No hay catálogos dados de alta.')

    def get_by_id(self):
        with MongoDBHandler('catalogs') as db:
            catalog = db.extract({'_id': ObjectId(self.id)}
                                 ) if objectid_validation(self.id) else None
            if catalog:
                return ok(CatalogSerializer(catalog[0]).data)
            return not_found('El catálogo no existe.')

    def delete(self):
        with MongoDBHandler('catalogs') as db:
            catalog = db.extract(
                {'_id': ObjectId(self.id)}) if objectid_validation(self.id) else None
            if catalog:
                db.delete({'_id': ObjectId(self.id)})
                return ok('Catálogo eliminado correctamente.')
            return bad_request('El catálogo no existe.')

    def update(self):
        with MongoDBHandler('catalogs') as db:
            required_fields = ['action', 'value']
            catalog = db.extract(
                {'_id': ObjectId(self.id)}) if objectid_validation(self.id) else None
            if catalog:
                if all(i in self.data for i in required_fields):
                    if self.data['action'] == 'add':
                        if self.data['value'] not in catalog[0]['values']:
                            catalog[0]['values'].append(self.data['value'])
                        else:
                            return bad_request(f"El valor '{self.data['value']}' ya existe en el catálogo.")
                    if self.data['action'] == 'delete':
                        if self.data['value'] in catalog[0]['values']:
                            catalog[0]['values'].remove(self.data['value'])
                        else:
                            return bad_request(f"'El valor {self.data['value']}' no está en la lista.")
                    db.update({'_id': ObjectId(self.id)}, {
                        'values': catalog[0]['values']})
                    return ok('El catálogo ha sido modificado con éxito.')
                return bad_request('Algunos campos requeridos no han sido completados.')
            return bad_request('El catálogo no existe.')
