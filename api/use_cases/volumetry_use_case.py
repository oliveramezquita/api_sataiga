from api_sataiga.handlers.mongodb_handler import MongoDBHandler
from api.helpers.validations import objectid_validation
from bson import ObjectId
from api.helpers.http_responses import created, bad_request, ok, not_found
from api.serializers.volumetry_serializer import VolumetrySerializer
from urllib.parse import parse_qs


class VolumetryUseCase:
    def __init__(self, request=None, **kwargs):
        if request:
            params = parse_qs(request.META['QUERY_STRING'])
            self.client_id = params['client_id'][0] if 'client_id' in params else None
            self.front = params['front'][0] if 'front' in params else None

        self.data = kwargs.get('data', None)
        self.id = kwargs.get('id', None)

    def __client_validation(self, db, client_id):
        client = MongoDBHandler.find(db, 'clients', {'_id': ObjectId(
            client_id), 'type': 'VS'}) if objectid_validation(client_id) else None
        if client:
            return True
        return False

    def __material_validation(self, db, material_id):
        material = MongoDBHandler.find(db, 'materials', {'_id': ObjectId(
            material_id)}) if objectid_validation(material_id) else None
        if material:
            return True
        return False

    def __calculate_totals(self):
        gran_total = 0
        for item in self.data['volumetry']:
            total = sum(int(q) for prototype in item['prototypes']
                        for q in prototype['quantities'].values())
            item['total'] = total
            gran_total += total

        self.data['gran_total'] = gran_total
        return self.data

    def save(self):
        with MongoDBHandler('volumetries') as db:
            required_fields = ['client_id',
                               'front', 'material_id', 'volumetry']
            if all(i in self.data for i in required_fields):
                if self.__client_validation(db, self.data['client_id']) and self.__material_validation(db, self.data['material_id']):
                    db.insert(self.__calculate_totals())
                    volumetries = db.extract(
                        {'client_id': self.data['client_id'], 'front': self.data['front']})
                    return ok(VolumetrySerializer(volumetries, many=True).data)
                return bad_request('Error al momento de procesar la información: el cliente o el material no existen.')
            return bad_request('Algunos campos requeridos no han sido completados.')

    def get(self):
        with MongoDBHandler('volumetries') as db:
            if self.client_id and self.front:
                volumetries = db.extract(
                    {'client_id': self.client_id, 'front': self.front})
                return ok(VolumetrySerializer(volumetries, many=True).data)
            return not_found('No existe volumería con lo datos asignados.')
