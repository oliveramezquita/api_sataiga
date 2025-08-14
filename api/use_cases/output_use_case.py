import traceback
from api.helpers.http_responses import bad_request, created, ok_paginated, ok, not_found
from api_sataiga.handlers.mongodb_handler import MongoDBHandler
from api.serializers.output_serializer import OutputSerializer
from django.core.paginator import Paginator
from urllib.parse import parse_qs
from api.constants import DEFAULT_PAGE_SIZE
from bson import ObjectId
from api.helpers.validations import objectid_validation
from datetime import datetime, timedelta


class OutputUseCase:
    def __init__(self, request=None, **kwargs):
        if request:
            params = parse_qs(request.META['QUERY_STRING'])
            self.page = params['page'][0] if 'page' in params else 1
            self.page_size = params['itemsPerPage'][0] \
                if 'itemsPerPage' in params else DEFAULT_PAGE_SIZE
            self.q = params['q'][0] if 'q' in params else None
            self.created_at = params['created_at'][0] if 'created_at' in params else None
        self.data = kwargs.get('data', [])
        self.id = kwargs.get('id', None)
        self.material_id = kwargs.get('material', None)

    def __update_iq(self, db):
        for item in self.data['items']:
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

    def __refund_output(self, db, items):
        for item in items:
            inventory = MongoDBHandler.find(
                db, 'inventory', {'material.id': item['id']})
            if inventory and len(inventory) > 0:
                quantity = float(
                    inventory[0]['quantity']) + float(item['quantity'])
                MongoDBHandler.modify(db, 'inventory', {'_id': inventory[0]['_id']}, {
                    'quantity': round(float(quantity), 2)
                })
            for source in item['source']:
                iq = MongoDBHandler.find(db, 'inventory_quantity', {
                                         '_id': ObjectId(source['iq_id'])})
                if iq and len(iq) > 0:
                    new_quantity = float(
                        iq[0]['quantity']) + float(source['output'])
                    status = 1 if iq[0]['status'] == 1 else 0
                    MongoDBHandler.modify(db, 'inventory_quantity', {'_id': iq[0]['_id']}, {
                        'quantity': round(float(new_quantity), 2),
                        'status': status
                    })

    def __set_update_responses(self):
        status_responses = [
            'La salida ha sido solicitada correctamente.',
            'La salida fue aprobada correctamente.',
            'Devolución solicitada.',
            'Devolución parcial aprobada correctamente.',
            'Devolución total aprobada correctamente.',
            'La salida fue cancelada correctamente.',
        ]
        if 'status' in self.data:
            return status_responses[int(self.data['status'])]
        return 'La salida ha sido actualizada correctamente.'

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
                    data['selected_items'] = []
                    data['folio'] = db.set_next_folio('output')
                    data['status'] = 0
                    id = db.insert(data)
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
            output = db.extract(
                {'_id': ObjectId(self.id)}) if objectid_validation(self.id) else None
            if output:
                return ok(OutputSerializer(output[0]).data)
            return not_found('La salida no existe.')

    def get_by_material(self):
        query = {'status': {'$in': list(range(6))}}
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
                    query['updated_at'] = {
                        '$gte': start_date, '$lt': end_date}
                else:
                    single_date = datetime.strptime(
                        created_at_param, '%Y-%m-%d')
                    next_day = single_date + timedelta(days=1)
                    query['updated_at'] = {
                        '$gte': single_date, '$lt': next_day}
            except ValueError as e:
                return bad_request(f'Error al parsear la fecha: {created_at_param} — {e}')

        inbounds = OutputUseCase.get_by_external(self.material_id, query)
        if inbounds:
            return ok(inbounds)
        return ok([])

    def update(self):
        with MongoDBHandler('outputs') as db:
            output = db.extract(
                {'_id': ObjectId(self.id)}) if objectid_validation(self.id) else None
            if output:
                if 'status' in self.data:
                    if self.data['status'] == 1:
                        self.data['items'] = [d for d in output[0]['items']
                                              if d['id'] in self.data['selected_items']]
                        self.data['selected_items'] = []
                        self.__update_iq(db)
                    if self.data['status'] == 3 or self.data['status'] == 4:
                        self.__refund_output(
                            db, [d for d in output[0]['items'] if d['id'] in self.data['selected_items']])
                        self.data['items'] = [d for d in output[0]['items'] if d['id']
                                              not in self.data['selected_items']] if self.data['status'] == 3 else self.data['items']
                        self.data['selected_items'] = []
                db.update({'_id': ObjectId(self.id)}, self.data)
                return ok(self.__set_update_responses())
            return not_found('La salida no existe.')

    @staticmethod
    def get_by_external(material_id, query):
        with MongoDBHandler('outputs') as db:
            outputs = db.extract(query, 'updated_at', -1)
            if outputs:
                result = [output for output in outputs if any(
                    item["id"] == material_id for item in output.get("items", []))]
                return OutputSerializer(result, many=True).data
            return []
