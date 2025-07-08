from urllib.parse import parse_qs
from api.constants import DEFAULT_PAGE_SIZE
from api_sataiga.handlers.mongodb_handler import MongoDBHandler
from django.core.paginator import Paginator
from api.helpers.http_responses import ok_paginated, ok
from api.serializers.inbound_serializer import InboundSerializer


class InboundUseCase:
    def __init__(self, request=None, **kwargs):
        if request:
            params = parse_qs(request.META['QUERY_STRING'])
            self.page = params['page'][0] if 'page' in params else 1
            self.page_size = params['itemsPerPage'][0] \
                if 'itemsPerPage' in params else DEFAULT_PAGE_SIZE
            self.q = params['q'][0] if 'q' in params else None
            self.supplier = params['supplier'][0] if 'supplier' in params else None
        self.data = kwargs.get('data', None)
        self.project_type = kwargs.get('project_type', None)

    def perform_counting(self, db, project, items):
        for item in items:
            material = {
                'id': item['material_id'],
                'color': item['color'],
                'concept': item['concept'],
                'measurement': item['measurement'],
                'sku': item['sku'],
                'supplier_id': item['supplier_id'],
                'supplier_code': item['supplier_code'],
                'inventory_price': item['inventory_price'],
                'market_price': item['market_price'],
                'presentation': item['presentation'],
                'reference': item['reference'],
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
                'material': material,
                'project': project,
                'quantity': round(float(item['delivered']['quantity']), 2)
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
        print(self.project_type)
        if self.project_type == 'Vivienda en Serie':
            results = self.__get_home_production()
        # TODO - Get from special projects
        return ok(results)

    @staticmethod
    def register(purchase_order_id, project, items):
        with MongoDBHandler('inbounds') as db:
            db.insert({
                'purchase_order_id': purchase_order_id,
                'project': project,
                'items': items,
            })
            use_case = InboundUseCase()
            use_case.perform_counting(db, project, items)
