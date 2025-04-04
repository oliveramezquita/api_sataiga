import re
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

    def __client_validation(self, db):
        client = MongoDBHandler.find(db, 'clients', {'_id': ObjectId(
            self.data['client_id']), 'type': 'VS'}) if objectid_validation(self.data['client_id']) else None
        if client:
            return True
        return False

    def __material_validation(self, db):
        material = MongoDBHandler.find(db, 'materials', {'_id': ObjectId(
            self.data['material_id'])}) if objectid_validation(self.data['material_id']) else None
        if material:
            return material
        return False

    def __calculate_totals(self):
        gran_total = 0
        pattern = re.compile(r'^\d+(\.\d{1,2})?$')
        for item in self.data['volumetry']:
            total = sum(
                float(q) if isinstance(q, (int, float, str)) and pattern.match(
                    str(q)) else 0
                for prototype in item['prototypes']
                for q in prototype['quantities'].values()
            )
            item['total'] = total
            gran_total += total

        self.data['gran_total'] = gran_total
        return self.data

    def save(self):
        with MongoDBHandler('volumetries') as db:
            required_fields = ['client_id',
                               'front', 'material_id', 'volumetry']
            if all(i in self.data for i in required_fields):
                material = self.__material_validation(db)
                if self.__client_validation(db) and material:
                    is_exist = db.extract(
                        {'client_id': self.data['client_id'], 'front': self.data['front'], 'material_id': self.data['material_id']})
                    if is_exist:
                        db.update({
                            'client_id': self.data['client_id'],
                            'front': self.data['front'],
                            'material_id': self.data['material_id']},
                            self.__calculate_totals())
                        message = f'El material: {material[0]['name']} ha sido actualizado correctamente en la volumetría.'
                    else:
                        db.insert(self.__calculate_totals())
                        message = f'El material: {material[0]['name']} ha sido añadido correctamente en la volumetría.'
                    volumetries = db.extract({
                        'client_id': self.data['client_id'],
                        'front': self.data['front']})
                    return ok({'data': VolumetrySerializer(volumetries, many=True).data, 'message': message})
                return bad_request('Error al momento de procesar la información: el cliente o el material no existen.')
            return bad_request('Algunos campos requeridos no han sido completados.')

    def get(self):
        with MongoDBHandler('volumetries') as db:
            if self.client_id and self.front:
                volumetries = db.extract(
                    {'client_id': self.client_id, 'front': self.front})
                return ok(VolumetrySerializer(volumetries, many=True).data)
            return not_found('No existe volumería con lo datos asignados.')

    def delete(self):
        with MongoDBHandler('volumetries') as db:
            volumetry = db.extract(
                {'_id': ObjectId(self.id)}) if objectid_validation(self.id) else None
            if volumetry:
                db.delete({'_id': ObjectId(self.id)})
                return ok('El elemento de la volumetría ha sido eliminado correctamente.')
            return bad_request('El elmemento de la volumetría no existe.')
