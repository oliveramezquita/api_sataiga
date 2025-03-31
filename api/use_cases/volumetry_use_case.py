from api_sataiga.handlers.mongodb_handler import MongoDBHandler
from api.helpers.validations import objectid_validation
from bson import ObjectId
from api.helpers.http_responses import created, bad_request


class VolumetryUseCase:
    def __init__(self, data=None, id=None):
        self.data = data
        self.id = id

    def __client_validation(self, db, client_id):
        client = MongoDBHandler.find(db, 'clients', {'_id': ObjectId(
            client_id), 'type': 'VS'}) if objectid_validation(client_id) else None
        if client:
            return True
        return False

    def __material_validation(self, db, material_id):
        material = MongoDBHandler.find(db, 'materials', {'_id': ObjectId(
            material_id), 'type': 'VS'}) if objectid_validation(material_id) else None
        if material:
            return True
        return False

    def save(self):
        with MongoDBHandler('volumetries') as db:
            required_fields = ['client_id',
                               'front', 'material_id', 'volumetry']
            if all(i in self.data for i in required_fields):
                if self.__client_validation(db, self.data['client_id']) and self.__material_validation(db, self.data['material_id']):
                    db.insert(self.data)
                    return created('Volumetría creada correctamente.')
                return bad_request('Error al momento de procesar la información: el cliente o el material no existen.')
            return bad_request('Algunos campos requeridos no han sido completados.')
