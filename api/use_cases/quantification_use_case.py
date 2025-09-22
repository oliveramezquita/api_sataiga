from urllib.parse import parse_qs
from api_sataiga.handlers.mongodb_handler import MongoDBHandler
from api.serializers.quantification_serializer import QuantificationSerializer
from api.helpers.http_responses import ok, not_found, bad_request
from collections import defaultdict
from bson import ObjectId
from api.helpers.validations import objectid_validation
from api.use_cases.inventory_use_case import InventoryUseCase


class QuantificationUseCase:
    def __init__(self, request=None, **kwargs):
        if request:
            params = parse_qs(request.META['QUERY_STRING'])
            self.client_id = params['client_id'][0] if 'client_id' in params else None
            self.front = params['front'][0] if 'front' in params else None
            self.prototype = params['prototype'][0] if 'prototype' in params else None
            self.availability = params['get_availability'][0] if 'get_availability' in params else False
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

    def __get_material_info(self, db, data):
        for area, materials in data['quantification'].items():
            for i, material in enumerate(materials):
                ms = MongoDBHandler.find(
                    db, 'materials', {'_id': ObjectId(
                        material['material_id'])},
                    projection={
                        "color": 1,
                        "concept": 1,
                        "measurement": 1,
                        "supplier_id": 1,
                        "supplier_code": 1,
                        "inventory_price": 1,
                        "market_price": 1,
                        "sku": 1,
                        "presentation": 1,
                        "reference": 1,
                        "division": 1
                    })
                data['quantification'][area][i]['material'] = (
                    {k: v for k, v in ms[0].items() if k != '_id'} if len(
                        ms) > 0 else None
                )
        return data

    def __get_material_availability(self, data):
        for area, materials in data['quantification'].items():
            for i, material in enumerate(materials):
                data['quantification'][area][i]['total_output'] = 0
                data['quantification'][area][i]['availability'] = InventoryUseCase.get_material_availability(
                    material['id'])

                # if 'COCINA' in data['quantification'][area][i]:
                #     data['quantification'][area][i]['TOTAL'] = data['quantification'][area][i]['COCINA']
        for key, items in list(data['quantification'].items()):
            data['quantification'][key] = [
                item for item in items if item.get("availability")]
            if not data['quantification'][key]:
                del data['quantification'][key]
        return data

    def get(self):
        with MongoDBHandler('quantification') as db:
            quantification = db.extract({
                'client_id': self.client_id,
                'front': self.front,
                'prototype': self.prototype})
            if quantification:
                q = self.__get_material_availability(
                    quantification[0]) if self.availability else quantification[0]
                return ok(QuantificationSerializer(self.__get_material_info(db, q)).data)
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
