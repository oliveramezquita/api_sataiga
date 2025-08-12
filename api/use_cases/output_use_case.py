import traceback
from api.helpers.http_responses import bad_request, created, ok_paginated, ok, not_found
from api_sataiga.handlers.mongodb_handler import MongoDBHandler
from api.serializers.output_serializer import OutputSerializer
from django.core.paginator import Paginator
from urllib.parse import parse_qs
from api.constants import DEFAULT_PAGE_SIZE
from bson import ObjectId
from api.helpers.validations import objectid_validation


class OutputUseCase:
    def __init__(self, request=None, **kwargs):
        if request:
            params = parse_qs(request.META['QUERY_STRING'])
            self.page = params['page'][0] if 'page' in params else 1
            self.page_size = params['itemsPerPage'][0] \
                if 'itemsPerPage' in params else DEFAULT_PAGE_SIZE
            self.q = params['q'][0] if 'q' in params else None
        self.data = kwargs.get('data', [])
        self.id = kwargs.get('id', None)

    def __update_iq(self, db, items):
        for item in items:
            inventory = MongoDBHandler.find(
                db, 'inventory', {'material.id': item['id']})
            if inventory and len(inventory) > 0:
                quantity = float(
                    inventory[0]['quantity']) - float(item['quantity'])
                MongoDBHandler.modify(db, 'inventory', {'_id': inventory[0]['_id']}, {
                    'quantity': round(float(quantity), 2)
                })
            for source in item['source']:
                iq = MongoDBHandler.find(db, 'inventory_quantity', {
                                         '_id': ObjectId(source['iq_id'])})
                if iq and len(iq) > 0:
                    status = 1 if float(source['output']) < float(
                        iq[0]['quantity']) else 2
                    new_quantity = float(
                        iq[0]['quantity']) - float(source['output'])
                    MongoDBHandler.modify(db, 'inventory_quantity', {'_id': iq[0]['_id']}, {
                        'quantity': round(float(new_quantity), 2),
                        'status': status
                    })

    def save(self):
        if 'outputs' in self.data:
            try:
                outputs = [
                    {
                        'id': item['id'],
                        'material': item['material'],
                        'quantity': item['total_output'],
                        'source': [
                            {
                                'iq_id': av['_id'],
                                'output': av['output'],
                                'project': av['project'],
                                'rack': av['rack'],
                                'level': av['level'],
                                'module': av['module'],
                            }
                            for av in item['availability']
                        ]
                    }
                    for item in self.data['outputs']
                ]
                self.data['items'] = outputs
                del self.data['outputs']
                with MongoDBHandler('outputs') as db:
                    data = self.data
                    data['folio'] = db.set_next_folio('output')
                    id = db.insert(data)
                    if id:
                        self.__update_iq(db, data['items'])
                    return created({'id': str(id)})
            except Exception as e:
                return bad_request(f'Error: {str(e)}, "Trace": {traceback.format_exc()}')
        return bad_request('Algunos campos requeridos no han sido completados.')

    def get(self):
        with MongoDBHandler('outputs') as db:
            # TODO - Add filters
            outputs = db.extract()
            paginator = Paginator(outputs, per_page=self.page_size)
            page = paginator.get_page(self.page)
            return ok_paginated(
                paginator,
                page,
                OutputSerializer(page.object_list, many=True).data
            )

    def get_by_id(self):
        with MongoDBHandler('outputs') as db:
            inbound = db.extract(
                {'_id': ObjectId(self.id)}) if objectid_validation(self.id) else None
            if inbound:
                return ok(OutputSerializer(inbound[0]).data)
            return not_found('La salida no existe.')
