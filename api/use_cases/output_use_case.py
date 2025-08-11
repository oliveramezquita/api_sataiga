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

    def save(self):
        if 'outputs' in self.data:
            try:
                outputs = [
                    {
                        'id': i,
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
                    for i, item in enumerate(self.data['outputs'])
                ]
                self.data['items'] = outputs
                del self.data['outputs']
                with MongoDBHandler('outputs') as db:
                    data = self.data
                    data['folio'] = db.set_next_folio('output')
                    id = db.insert(data)
                    # TODO: Remove amount in inventory and update inventory_quantity
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
