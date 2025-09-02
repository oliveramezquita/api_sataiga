from urllib.parse import parse_qs
from api.constants import DEFAULT_PAGE_SIZE
from api_sataiga.handlers.mongodb_handler import MongoDBHandler
from django.core.paginator import Paginator
from api.helpers.http_responses import ok, ok_paginated, not_found, bad_request
from api.serializers.inventory_serializer import InventorySerializer
from api.serializers.inventory_quantity_serializer import InventoryQuantitySerializer
from bson import ObjectId
from api.helpers.validations import objectid_validation
from openpyxl import Workbook
from django.http import HttpResponse


class InventoryUseCase:
    def __init__(self, request=None, **kwargs):
        if request:
            self.request = request
            params = parse_qs(request.META['QUERY_STRING'])
            self.page = params['page'][0] if 'page' in params else 1
            self.page_size = params['itemsPerPage'][0] \
                if 'itemsPerPage' in params else DEFAULT_PAGE_SIZE
            self.q = params['q'][0] if 'q' in params else None
            self.available = params['available'][0] if 'available' in params else False
            self.supplier = params['supplier'][0] if 'supplier' in params else None
            self.order_by = - \
                1 if 'orderBy' in params and params['orderBy'][0] == 'desc' else 1
        self.data = kwargs.get('data', None)
        self.id = kwargs.get('id', None)
        self.supplier_id = kwargs.get('supplier_id', None)
        self.material_id = kwargs.get('material_id', None)

    def __suppliers_list(self):
        with MongoDBHandler('suppliers') as db:
            suppliers_list = {}
            suppliers = db.extract()
            if suppliers:
                for supplier in suppliers:
                    suppliers_list[str(supplier['_id'])] = supplier['name']
            return suppliers_list

    def __get_quantities(self, inventory_id):
        with MongoDBHandler('inventory_quantity') as db:
            return db.extract({'inventory_id': inventory_id})

    def __validate_value(self, material, key):
        if key in material:
            return material[key]
        return None

    def __export_materials(self, inventory):
        suppliers_list = self.__suppliers_list()
        wb = Workbook()
        ws = wb.active
        ws.title = "Inventario"

        headers = [
            'RACK', 'NIVEL', 'MÓDULO', 'PROVEEDOR', 'CÓDIGO PROVEEDOR',
            'SKU', 'PROYECTO', 'CONCEPTO', 'UNIDAD', 'TOTAL']
        ws.append(headers)

        for item in inventory:
            for quantity in self.__get_quantities(str(item['_id'])):
                ws.append([
                    self.__validate_value(quantity, 'rack'),
                    self.__validate_value(quantity, 'level'),
                    self.__validate_value(quantity, 'module'),
                    suppliers_list[item['material']['supplier_id']],
                    self.__validate_value(item['material'], 'supplier_code'),
                    item['material']['sku'],
                    'STOCK' if quantity['project']['type'] == 'Stock' else quantity['project']['name'],
                    item['material']['concept'],
                    item['material']['measurement'],
                    float(quantity['quantity']),
                ])

        response = HttpResponse(
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = 'attachment; filename=inventario.xlsx'
        wb.save(response)
        return response

    def __remove_inbounds(self, db, inbound_id, material_id):
        if not objectid_validation(inbound_id) or not material_id:
            return

        filters = {
            "_id": ObjectId(inbound_id),
            "items.material_id": material_id
        }

        inbounds = MongoDBHandler.find(db, 'inbounds', filters)
        if not inbounds:
            return

        for inbound in inbounds:
            items = inbound.get("items", [])
            new_items = [item for item in items if item.get(
                "material_id") != material_id]

            if new_items:
                MongoDBHandler.modify(
                    db,
                    'inbounds',
                    {'_id': inbound["_id"]},
                    {'items': new_items}
                )
            else:
                MongoDBHandler.remove(db, 'inbounds', {'_id': inbound["_id"]})

    def __remove_quantities(self, db):
        inventory_quantity = MongoDBHandler.find(
            db, 'inventory_quantity', {'inventory_id': self.id})
        if inventory_quantity:
            for iq in inventory_quantity:
                self.__remove_inbounds(db, iq['inbound_id'], iq['material_id'])
            MongoDBHandler.remove(db, 'inventory_quantity', {
                                  'inventory_id': self.id})

    def get(self):
        with MongoDBHandler('inventory') as db:
            filters = {}
            if self.q:
                filters['$or'] = [
                    {'material.concept': {'$regex': self.q, '$options': 'i'}},
                    {'material.measurement': {'$regex': self.q, '$options': 'i'}},
                    {'material.supplier_code': {'$regex': self.q, '$options': 'i'}},
                    {'material.sku': {'$regex': self.q, '$options': 'i'}},
                    {'material.presentation': {'$regex': self.q, '$options': 'i'}},
                    {'material.reference': {'$regex': self.q, '$options': 'i'}},
                ]
            if self.available:
                filters['quantity'] = {'$gt': 0}
            if self.supplier:
                filters['material.supplier_id'] = self.supplier
            items = db.extract(filters, 'material.concept', self.order_by)
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

    def download(self):
        with MongoDBHandler('inventory') as db:
            filters = {}
            if self.supplier:
                filters['material.supplier_id'] = self.supplier
            materials = db.extract(filters)
            return self.__export_materials(materials)

    def delete(self):
        with MongoDBHandler('inventory') as db:
            material = db.extract(
                {'_id': ObjectId(self.id)}) if objectid_validation(self.id) else None
            if material:
                self.__remove_quantities(db)
                db.delete({'_id': ObjectId(self.id)})
                return ok(f'El material: {material[0]['material']['concept']} fue eliminado correctamente del inventario.')
            return bad_request('El material no existe en el inventario.')

    @staticmethod
    def get_material_availability(material_id):
        with MongoDBHandler('inventory_quantity') as db:
            filters = {'material_id': material_id, 'status': {'$lt': 2}}
            iq = db.extract(filters)
            if len(iq) > 0:
                return InventoryQuantitySerializer(iq, many=True).data
            return []
