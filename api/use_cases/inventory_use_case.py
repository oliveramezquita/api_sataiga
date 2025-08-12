from urllib.parse import parse_qs
from api.constants import DEFAULT_PAGE_SIZE
from api_sataiga.handlers.mongodb_handler import MongoDBHandler
from django.core.paginator import Paginator
from api.helpers.http_responses import ok, ok_paginated, not_found
from api.serializers.inventory_serializer import InventorySerializer
from api.serializers.inventory_quantity_serializer import InventoryQuantitySerializer
from bson import ObjectId
from api.helpers.validations import objectid_validation


class InventoryUseCase:
    def __init__(self, request=None, **kwargs):
        if request:
            self.request = request
            params = parse_qs(request.META['QUERY_STRING'])
            self.page = params['page'][0] if 'page' in params else 1
            self.page_size = params['itemsPerPage'][0] \
                if 'itemsPerPage' in params else DEFAULT_PAGE_SIZE
            self.q = params['q'][0] if 'q' in params else None
            self.supplier = params['supplier'][0] if 'supplier' in params else None
        self.data = kwargs.get('data', None)
        self.id = kwargs.get('id', None)
        self.supplier_id = kwargs.get('supplier_id', None)
        self.material_id = kwargs.get('material_id', None)

    def get(self):
        with MongoDBHandler('inventory') as db:
            filters = {}
            if self.q:
                filters['$or'] = [
                    {'rack': {'$regex': self.q, '$options': 'i'}},
                    {'level': {'$regex': self.q, '$options': 'i'}},
                    {'module': {'$regex': self.q, '$options': 'i'}},
                    # {'sku': {'$regex': self.q, '$options': 'i'}},
                    # {'presentation': {'$regex': self.q, '$options': 'i'}},
                    # {'reference': {'$regex': self.q, '$options': 'i'}},
                ]
            if self.supplier:
                filters['material.supplier_id'] = self.supplier
            items = db.extract(filters)
            materials = []
            for item in items:
                item['availability'] = InventoryUseCase.get_material_availability(
                    item['material']['id'])
                materials.append(item)
            paginator = Paginator(materials, per_page=self.page_size)
            page = paginator.get_page(self.page)
            return ok_paginated(
                paginator,
                page,
                InventorySerializer(page.object_list, many=True).data
            )

    def get_by_id(self):
        with MongoDBHandler('inventory') as db:
            inventory = db.extract(
                {'_id': ObjectId(self.id)}) if objectid_validation(self.id) else None
            if inventory:
                return ok(InventorySerializer(inventory[0]).data)
            return not_found('El inventario no existe.')

    def get_by_material(self):
        return ok(InventoryUseCase.get_material_availability(self.material_id))

    @staticmethod
    def get_material_availability(material_id):
        with MongoDBHandler('inventory_quantity') as db:
            filters = {'material_id': material_id, 'status': {'$lt': 2}}
            iq = db.extract(filters)
            if len(iq) > 0:
                return InventoryQuantitySerializer(iq, many=True).data
            return []
