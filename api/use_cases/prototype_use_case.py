from urllib.parse import parse_qs
from api.constants import DEFAULT_PAGE_SIZE
from api_sataiga.handlers.mongodb_handler import MongoDBHandler
from api.helpers.http_responses import created, bad_request, ok, ok_paginated, not_found
from django.core.paginator import Paginator
from api.serializers.prototype_serializer import PrototypeSerializer
from bson import ObjectId
from api.helpers.validations import objectid_validation
from api.use_cases.catalog_use_case import CatalogUseCase


class PrototypeUseCase:
    def __init__(self, request=None, **kwargs):
        if request:
            params = parse_qs(request.META['QUERY_STRING'])
            self.page = params['page'][0] if 'page' in params else 1
            self.page_size = params['itemsPerPage'][0] \
                if 'itemsPerPage' in params else DEFAULT_PAGE_SIZE
            self.q = params['q'][0] if 'q' in params else None
        self.data = kwargs.get('data', None)
        self.id = kwargs.get('id', None)
        self.client_id = kwargs.get('client_id', None)
        self.front = kwargs.get('front', None)

    def __client_validation(self, db, client_id):
        client = MongoDBHandler.find(db, 'clients', {'_id': ObjectId(
            client_id), 'type': 'VS'}) if objectid_validation(client_id) else None
        if client:
            return client[0]
        return False

    def __update_volumetry(self, db):
        volumetry = MongoDBHandler.find(db, 'volumetries', {
                                        'client_id': self.data['client_id'], 'front': self.data['front']})
        if volumetry:
            for item in volumetry:
                for v in item["volumetry"]:
                    if not any(proto["prototype"] == self.data['name'] for proto in v["prototypes"]):
                        v["prototypes"].append({
                            "prototype": self.data['name'],
                            "quantities": {"factory": 0, "instalation": 0}
                        })
                MongoDBHandler.modify(
                    db,
                    'volumetries',
                    {'_id': ObjectId(item['_id'])},
                    {'volumetry': item["volumetry"]})

    def __delete_into_volumetry(self, db, **kwargs):
        volumetry = MongoDBHandler.find(
            db,
            'volumetries',
            {'client_id': kwargs.get('client_id'), 'front': kwargs.get('front')})
        if volumetry:
            for item in volumetry:
                for v in item["volumetry"]:
                    v["prototypes"] = [
                        proto for proto in v["prototypes"] if proto["prototype"] != kwargs.get('name')
                    ]
                    v["total"] = sum(float(q) for proto in v["prototypes"]
                                     for q in proto["quantities"].values())
                item["gran_total"] = sum(v["total"] for v in item["volumetry"])
                MongoDBHandler.modify(
                    db,
                    'volumetries',
                    {'_id': ObjectId(item['_id'])},
                    {'volumetry': item["volumetry"], 'gran_total': item["gran_total"]})

    def __check_prototype(self, db):
        prototype = MongoDBHandler.find(db, 'prototypes', {
            'client_id': self.data['client_id'],
            'name': self.data['name'],
            'front': self.data['front'],
        })
        if prototype:
            return False
        if 'client_name' in self.data:
            CatalogUseCase.external_update(
                'Frentes', {self.data['client_name']: self.data['front']})
            CatalogUseCase.external_update(
                'Prototipos', {self.data['client_name']: self.data['name']})
        return True

    def save(self):
        with MongoDBHandler('prototypes') as db:
            required_fields = ['client_id', 'name', 'front']
            if all(i in self.data for i in required_fields):
                if self.__client_validation(db, self.data['client_id']):
                    if self.__check_prototype(db):
                        db.insert(self.data)
                        # TODO: Create chicken like a prototype
                        # db.insert({
                        #     'client_id': self.data['client_id'],
                        #     'client_name': self.data['client_name'],
                        #     'front': self.data['front'],
                        #     'name': f"{self.data['name']} Cocina",
                        # })
                        self.__update_volumetry(db)
                        return created('Prototipo creado correctamente.')
                    return bad_request('El prototipo ya existe.')
                return bad_request('El cliente seleccionado no existe.')
            return bad_request('Algunos campos requeridos no han sido completados.')

    def get(self):
        with MongoDBHandler('prototypes') as db:
            filters = {}
            if self.q:
                filters['$or'] = [
                    {'name': {'$regex': self.q, '$options': 'i'}},
                    {'front': {'$regex': self.q, '$options': 'i'}},
                ]
            prototypes = db.extract(filters)
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
                    return ok(fronts)
                return not_found(f'No se encontraron frentes / fraccionamientos para el cliente: {client['name']}')
            return bad_request('El cliente seleccionado no existe.')

    def get_prototype_by_data(self):
        with MongoDBHandler('prototypes') as db:
            client = self.__client_validation(db, self.client_id)
            if client:
                results = db.extract(
                    {'client_id': self.client_id, 'front': self.front})
                if results:
                    prototypes = sorted(set(item["name"] for item in results))
                    return ok(prototypes)
                return not_found(f'No se encontraron prototipos para el cliente: {client['name']}, y el frente / fraccionamiento: {self.front}.')
            return bad_request('El cliente seleccionado no existe.')

    def update(self):
        with MongoDBHandler('prototypes') as db:
            prototype = db.extract(
                {'_id': ObjectId(self.id)}) if objectid_validation(self.id) else None
            if prototype:
                db.update({'_id': ObjectId(self.id)}, self.data)
                self.__update_volumetry(db)
                return ok('Prototipo actualizado correctamente.')
            return bad_request('El prototipo no existe.')

    def delete(self):
        with MongoDBHandler('prototypes') as db:
            prototype = db.extract(
                {'_id': ObjectId(self.id)}) if objectid_validation(self.id) else None
            if prototype:
                db.delete({'_id': ObjectId(self.id)})
                self.__delete_into_volumetry(db, **prototype[0])
                return ok('Prototipo eliminado correctamente.')
            return bad_request('El prototipo no existe.')
