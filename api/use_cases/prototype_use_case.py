from urllib.parse import parse_qs
from api.constants import DEFAULT_PAGE_SIZE
from api_sataiga.handlers.mongodb_handler import MongoDBHandler
from api.helpers.http_responses import created, bad_request, ok, ok_paginated, not_found
from django.core.paginator import Paginator
from api.serializers.prototype_serializer import PrototypeSerializer
from bson import ObjectId
from api.helpers.validations import objectid_validation


class PrototypeUseCase:
    def __init__(self, request=None, **kwargs):
        if request:
            params = parse_qs(request.META['QUERY_STRING'])
            self.page = params['page'][0] if 'page' in params else 1
            self.page_size = params['itemsPerPage'][0] \
                if 'itemsPerPage' in params else DEFAULT_PAGE_SIZE
            self.status = params['status'][0] if 'status' in params else None
        self.data = kwargs.get('data', None)
        self.id = kwargs.get('id', None)
        self.client_id = kwargs.get('client_id', None)

    def __client_validation(self, db, client_id):
        client = MongoDBHandler.find(db, 'clients', {'_id': ObjectId(
            client_id), 'type': 'VS'}) if objectid_validation(client_id) else None
        if client:
            return client[0]
        return False

    def __check_prototype(self, db, client_id, name, front):
        prototype = MongoDBHandler.find(db, 'prototypes', {
            'client_id': client_id,
            'name': name,
            'front': front,
        })
        if prototype:
            return False
        return True

    def save(self):
        with MongoDBHandler('prototypes') as db:
            required_fields = ['client_id', 'name', 'front']
            if all(i in self.data for i in required_fields):
                if self.__client_validation(db, self.data['client_id']):
                    if self.__check_prototype(db, **self.data):
                        db.insert(self.data)
                        return created('Prototipo creado correctamente.')
                    return bad_request('El prototipo ya existe.')
                return bad_request('El clinte seleccionado no existe.')
            return bad_request('Algunos campos requeridos no han sido completados.')

    def get(self):
        with MongoDBHandler('prototypes') as db:
            prototypes = db.extract()
            paginator = Paginator(prototypes, per_page=self.page_size)
            page = paginator.get_page(self.page)
            return ok_paginated(
                paginator,
                page,
                PrototypeSerializer(page.object_list, many=True).data
            )

    def get_by_client(self):
        with MongoDBHandler('prototypes') as db:
            client = self.__client_validation(db, self.client_id)
            if client:
                results = db.extract({'client_id': self.client_id})
                if results:
                    fronts = sorted(set(item["front"] for item in results))
                    prototypes = sorted(set(item["name"] for item in results))
                    return ok(
                        {
                            "fronts": fronts,
                            "prototypes": prototypes
                        }
                    )
                return not_found(f'No se encontraron protoripos para el cliente: {client['name']}')
            return bad_request('El clinte seleccionado no existe.')

    def update(self):
        with MongoDBHandler('prototypes') as db:
            prototype = db.extract(
                {'_id': ObjectId(self.id)}) if objectid_validation(self.id) else None
            if prototype:
                db.update({'_id': ObjectId(self.id)}, self.data)
                return ok('Prototipo actualizado correctamente.')
            return bad_request('El prototipo no existe.')

    def delete(self):
        with MongoDBHandler('prototypes') as db:
            prototype = db.extract(
                {'_id': ObjectId(self.id)}) if objectid_validation(self.id) else None
            if prototype:
                db.delete({'_id': ObjectId(self.id)})
                return ok('Prototipo eliminado correctamente.')
            return bad_request('El prototipo no existe.')
