from urllib.parse import parse_qs
from api_sataiga.handlers.mongodb_handler import MongoDBHandler
from api.serializers.quantification_serializer import QuantificationSerializer
from api.helpers.http_responses import ok, not_found, bad_request
from collections import defaultdict
from bson import ObjectId
from api.helpers.validations import objectid_validation


class QuantificationUseCase:
    def __init__(self, request=None, **kwargs):
        if request:
            params = parse_qs(request.META['QUERY_STRING'])
            self.client_id = params['client_id'][0] if 'client_id' in params else None
            self.front = params['front'][0] if 'front' in params else None
            self.prototype = params['prototype'][0] if 'prototype' in params else None
        self.data = kwargs.get('data', None)
        self.id = kwargs.get('id', None)
        self.action = kwargs.get('action', None)

    def __assign_color(self, quantification):
        if self.data['area'] in quantification:
            for idx, _ in enumerate(quantification[self.data['area']]):
                if quantification[self.data['area']][idx]['id'] in self.data['materials']:
                    quantification[self.data['area']
                                   ][idx]['material']['color'] = self.data['color']
        return quantification

    def __change_area(self, quantification):
        if self.data['area'] in quantification and self.data['destination'] in quantification:
            deleted = []
            for idx, _ in enumerate(quantification[self.data['area']]):
                if quantification[self.data['area']][idx]['id'] in self.data['materials']:
                    quantification[self.data['destination']].append(
                        quantification[self.data['area']][idx])
                    deleted.append(idx)
            quantification[self.data['area']] = [v for i, v in enumerate(
                quantification[self.data['area']]) if i not in deleted]
        return quantification

    def get(self):
        with MongoDBHandler('quantification') as db:
            quantification = db.extract({
                'client_id': self.client_id,
                'front': self.front,
                'prototype': self.prototype})
            if quantification:
                return ok(QuantificationSerializer(quantification[0]).data)
            return not_found("No se encontró la cuantificación para los datos proporcionados.")

    def filters(self):
        with MongoDBHandler('quantification') as db:
            quantification = db.extract({'client_id': self.client_id})
            if quantification:
                result = defaultdict(list)
                for item in quantification:
                    result[item['front']].append(item['prototype'])
                output = [{k: v} for k, v in result.items()]
                return ok(output)
            return not_found("No se encontraron elementos con el cliente proporcionado.")

    def update(self):
        with MongoDBHandler('quantification') as db:
            required_fields = ['area', 'materials']
            if self.action == 'assign_color':
                required_fields.append('color')
            elif self.action == 'change_area':
                required_fields.append('destination')
            else:
                return not_found('La actualización de la cuantificación no se encuentra.')

            if all(i in self.data for i in required_fields):
                quantification = db.extract(
                    {'_id': ObjectId(self.id)}) if objectid_validation(self.id) else None
                if quantification:
                    if self.action == 'assign_color':
                        quantification[0]['quantification'] = self.__assign_color(
                            quantification[0]['quantification'])
                    elif self.action == 'change_area':
                        quantification[0]['quantification'] = self.__change_area(
                            quantification[0]['quantification'])
                    db.update({'_id': ObjectId(self.id)}, {
                        'quantification': quantification[0]['quantification']})
                    return ok(QuantificationSerializer(quantification[0]).data)
                return not_found('No se encontro la cuantificación.')
            return bad_request('Algunos campos requeridos no han sido completados.')
