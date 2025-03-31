from urllib.parse import parse_qs
from api.constants import DEFAULT_PAGE_SIZE
from api_sataiga.handlers.mongodb_handler import MongoDBHandler
from api.helpers.http_responses import created, bad_request, ok, ok_paginated, not_found
from bson import ObjectId
from api.helpers.validations import objectid_validation
from django.core.paginator import Paginator
from api.serializers.material_serializer import MaterialSerializer


class MaterialUseCase:
    def __init__(self, request=None, **kwargs):
        if request:
            params = parse_qs(request.META['QUERY_STRING'])
            self.page = params['page'][0] if 'page' in params else 1
            self.page_size = params['itemsPerPage'][0] \
                if 'itemsPerPage' in params else DEFAULT_PAGE_SIZE
            self.status = params['status'][0] if 'status' in params else None
        self.data = kwargs.get('data', None)
        self.id = kwargs.get('id', None)

    def __check_supplier(self, db, supplier_id):
        supplier = MongoDBHandler.find(db, 'suppliers', {'_id': ObjectId(
            supplier_id)}) if objectid_validation(supplier_id) else None
        if supplier:
            return True
        return False

    def save(self):
        with MongoDBHandler('materials') as db:
            required_fields = ['name', 'supplier_id', 'measurement',
                               'unit_price', 'inventory_price', 'market_price', 'price_difference']
            if all(i in self.data for i in required_fields):
                if self.__check_supplier(db, self.data['supplier_id']):
                    if 'automation' not in self.data:
                        self.data['automation'] = False
                    db.insert(self.data)
                    return created('Material creado correctamente.')
                return bad_request('El proveedor selecionado no existe.')
            return bad_request('Algunos campos requeridos no han sido completados.')

    def get(self):
        with MongoDBHandler('materials') as db:
            materials = db.extract()
            paginator = Paginator(materials, per_page=self.page_size)
            page = paginator.get_page(self.page)
            return ok_paginated(
                paginator,
                page,
                MaterialSerializer(page.object_list, many=True).data
            )

    def get_by_id(self):
        with MongoDBHandler('materials') as db:
            material = db.extract(
                {'_id': ObjectId(self.id)}) if objectid_validation(self.id) else None
            if material:
                return ok(MaterialSerializer(material[0]).data)
            return not_found('El material no existe.')

    def update(self):
        with MongoDBHandler('materials') as db:
            material = db.extract(
                {'_id': ObjectId(self.id)}) if objectid_validation(self.id) else None
            if material:
                if 'supplier_id' in self.data and not self.__check_supplier(db, self.data['supplier_id']):
                    return bad_request('El proveedor selecionado no existe.')
                db.update({'_id': ObjectId(self.id)}, self.data)
                return ok('Material actualizado correctamente.')
            return bad_request('El material no existe.')

    def delete(self):
        with MongoDBHandler('materials') as db:
            material = db.extract(
                {'_id': ObjectId(self.id)}) if objectid_validation(self.id) else None
            if material:
                db.delete({'_id': ObjectId(self.id)})
                return ok('Material eliminado correctamente.')
            return bad_request('El material no existe.')
