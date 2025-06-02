from api_sataiga.handlers.mongodb_handler import MongoDBHandler
from api.helpers.http_responses import created, bad_request, ok, not_found
from api.serializers.catalog_serializer import CatalogSerializer
from bson import ObjectId
from api.helpers.validations import objectid_validation
from urllib.parse import parse_qs
from api.constants import DEFAULT_PAGE_SIZE
from django.core.paginator import Paginator


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
                if isinstance(self.data['values'], list):
                    self.data['values'] = [x for x in self.data['values'] if x]
                if len(self.data['values']) > 0:
                    id = db.insert(self.data)
                    return created({'id': str(id)})
                return bad_request('Inserte al menos un elemento al catálogo.')
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
            return not_found('El catálogo no existe.')

    def update(self):
        with MongoDBHandler('catalogs') as db:
            catalog = db.extract(
                {'_id': ObjectId(self.id)}) if objectid_validation(self.id) else None
            if catalog:
                if isinstance(self.data['values'], list):
                    self.data['values'] = [x for x in self.data['values'] if x]
                if len(self.data['values']) > 0:
                    db.update({'_id': ObjectId(self.id)}, self.data)
                    return ok('El catálogo ha sido modificado con éxito.')
                return bad_request('Inserte al menos un elemento al catálogo.')
            return not_found('El catálogo no existe.')

    @staticmethod
    def external_update(name, new_value):
        with MongoDBHandler('catalogs') as db:
            current_values = db.extract({'name': name})
            if current_values:
                if isinstance(new_value, dict):
                    for key, values in new_value.items():
                        if key in current_values[0]['values']:
                            if values not in current_values[0]['values'][key]:
                                current_values[0]['values'][key].append(values)
                        else:
                            current_values[0]['values'][key] = [values]
                elif isinstance(new_value, str):
                    if new_value not in current_values[0]['values']:
                        current_values[0]['values'].append(new_value)
                db.update({'name': name}, {
                          'values': current_values[0]['values']})
