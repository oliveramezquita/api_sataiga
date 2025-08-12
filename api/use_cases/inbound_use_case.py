from urllib.parse import parse_qs
from api.constants import DEFAULT_PAGE_SIZE
from api_sataiga.handlers.mongodb_handler import MongoDBHandler
from django.core.paginator import Paginator
from api.helpers.http_responses import ok_paginated, ok, created, bad_request, not_found
from api.serializers.inbound_serializer import InboundSerializer
from api.serializers.inventory_quantity_serializer import InventoryQuantitySerializer
from bson import ObjectId
from api.helpers.validations import objectid_validation
from datetime import datetime, timedelta


class InboundUseCase:
    def __init__(self, request=None, **kwargs):
        if request:
            params = parse_qs(request.META['QUERY_STRING'])
            self.page = params['page'][0] if 'page' in params else 1
            self.page_size = params['itemsPerPage'][0] \
                if 'itemsPerPage' in params else DEFAULT_PAGE_SIZE
            self.q = params['q'][0] if 'q' in params else None
            self.supplier = params['supplier'][0] if 'supplier' in params else None
            self.created_at = params['created_at'][0] if 'created_at' in params else None
        self.data = kwargs.get('data', None)
        self.id = kwargs.get('id', None)
        self.project_type = kwargs.get('project_type', None)
        self.material_id = kwargs.get('material', None)

    def perform_counting(self, db, project, items, inbound_id):
        for item in items:
            material = {
                'id': item['material_id'],
                'color': item.get('color', ''),
                'concept': item['concept'],
                'measurement': item['measurement'],
                'sku': item['sku'],
                'division': item.get['division'],
                'supplier_id': item['supplier_id'],
                'supplier_code': item.get('supplier_code', ''),
                'inventory_price': item.get('inventory_price', ''),
                'market_price': item.get('market_price', ''),
                'presentation': item.get('presentation', ''),
                'reference': item.get('reference', ''),
            }
            inventory = MongoDBHandler.find(
                db, 'inventory', {'material.id': item['material_id']})
            inventory_id = None
            if inventory and len(inventory) > 0:
                inventory_id = str(inventory[0]['_id'])
                quantity = float(inventory[0]['quantity']) + \
                    float(item['delivered']['quantity'])
                MongoDBHandler.modify(db, 'inventory', {'_id': inventory[0]['_id']}, {
                    'quantity': round(float(quantity), 2)
                })
            if not inventory_id:
                inventory_id = MongoDBHandler.record(db, 'inventory', {
                    'material': material,
                    'quantity': item['delivered']['quantity'],
                })
            MongoDBHandler.record(db, 'inventory_quantity', {
                'inventory_id': str(inventory_id),
                'inbound_id': str(inbound_id),
                'material_id': material['id'],
                'project': project,
                'quantity': round(float(item['delivered']['quantity']), 2),
                'rack': item['delivered']['rack'],
                'level': item['delivered']['level'],
                'module': item['delivered']['module'],
                'status': 0,
            })

    def get(self):
        with MongoDBHandler('inbounds') as db:
            # TODO - Add filters
            inbounds = db.extract()
            paginator = Paginator(inbounds, per_page=self.page_size)
            page = paginator.get_page(self.page)
            return ok_paginated(
                paginator,
                page,
                InboundSerializer(page.object_list, many=True).data
            )

    def __get_home_production(self):
        results = []
        with MongoDBHandler('home_production') as db:
            home_production = db.extract()
            if home_production:
                results = [{"_id": str(
                    item["_id"]), "name": f"{item['front']} - {item['od']}"} for item in home_production]
        return results

    def get_project(self):
        results = []
        if self.project_type == 'Vivienda en Serie':
            results = self.__get_home_production()
        # TODO - Get from special projects
        return ok(results)

    def save(self):
        with MongoDBHandler('inbounds') as db:
            required_fields = ['project', 'items']
            if all(i in self.data for i in required_fields):
                # TODO - Calculate the total of new materials added
                data = self.data
                data['folio'] = db.set_next_folio('inbound')
                id = db.insert(data)
                self.perform_counting(db, data['project'], data['items'], id)
                return created({'id': str(id)})
            return bad_request('Algunos campos requeridos no han sido completados.')

    def get_by_id(self):
        with MongoDBHandler('inbounds') as db:
            inbound = db.extract(
                {'_id': ObjectId(self.id)}) if objectid_validation(self.id) else None
            if inbound:
                return ok(InboundSerializer(inbound[0]).data)
            return not_found('La entrada no existe.')

    def get_by_material(self):
        with MongoDBHandler('inventory_quantity') as db:
            query = {'material_id': self.material_id}
            created_at_param = None
            if self.created_at:
                created_at_param = self.created_at.replace(' to ', '+to+')

            if isinstance(created_at_param, str):
                try:
                    if '+to+' in created_at_param:
                        start_str, end_str = created_at_param.split('+to+')
                        start_date = datetime.strptime(start_str, '%Y-%m-%d')
                        end_date = datetime.strptime(
                            end_str, '%Y-%m-%d') + timedelta(days=1)
                        query['created_at'] = {
                            '$gte': start_date, '$lt': end_date}
                    else:
                        single_date = datetime.strptime(
                            created_at_param, '%Y-%m-%d')
                        next_day = single_date + timedelta(days=1)
                        query['created_at'] = {
                            '$gte': single_date, '$lt': next_day}
                except ValueError as e:
                    return bad_request(f'Error al parsear la fecha: {created_at_param} — {e}')
            inbounds = db.extract(query)

            if inbounds:
                return ok(InventoryQuantitySerializer(inbounds, many=True).data)
            return ok([])

    def delete(self):
        with MongoDBHandler('inbounds') as db:
            material = db.extract(
                {'_id': ObjectId(self.id)}) if objectid_validation(self.id) else None
            if material:
                db.delete({'_id': ObjectId(self.id)})
                return ok('Entrada eliminada correctamente.')
            return bad_request('La entrada no existe.')

    @staticmethod
    def register(purchase_order_id, supplier_id, project, items, folio):
        with MongoDBHandler('inbounds') as db:
            inbound_id = db.insert({
                'purchase_order_id': purchase_order_id,
                'supplier_id': supplier_id,
                'project': project,
                'items': items,
                'folio': folio,
            })
            use_case = InboundUseCase()
            use_case.perform_counting(db, project, items, inbound_id)
