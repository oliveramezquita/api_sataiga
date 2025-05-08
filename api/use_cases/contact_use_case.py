from api_sataiga.handlers.mongodb_handler import MongoDBHandler
from api.helpers.http_responses import created, bad_request, ok, not_found
from api.serializers.contact_serializer import ContactSerializer
from bson import ObjectId
from api.helpers.validations import objectid_validation


class ContactUseCase:
    def __init__(self, request=None, **kwargs):
        self.client_id = kwargs.get('client_id', None)
        self.data = kwargs.get('data', None)
        self.id = kwargs.get('id', None)

    def __client_validation(self, db):
        client = MongoDBHandler.find(db, 'clients', {'_id': ObjectId(
            self.client_id)}) if objectid_validation(self.client_id) else None
        if client:
            return client[0]
        return False

    def save(self):
        with MongoDBHandler('contacts') as db:
            if self.__client_validation(db):
                if 'name' in self.data:
                    db.insert({
                        'client_id': self.client_id,
                        **self.data})
                    return created('Proveedor creado correctamente.')
                return bad_request('Algunos campos requeridos no han sido completados.')
            return bad_request('Error al momento de procesar la información: el cliente no existen.')

    def get(self):
        with MongoDBHandler('contacts') as db:
            if self.__client_validation(db):
                contacts = db.extract({'client_id': self.client_id})
                if contacts:
                    return ok(ContactSerializer(contacts, many=True).data)
                return not_found('No existen contactos hasta el momento para el cliente seleccionado.')
            return bad_request('Error al momento de procesar la información: el cliente no existen.')

    def update(self):
        with MongoDBHandler('contacts') as db:
            contact = db.extract(
                {'_id': ObjectId(self.id)}) if objectid_validation(self.id) else None
            if contact:
                db.update({'_id': ObjectId(self.id)}, self.data)
                return ok('Contacto actualizado correctamente.')
            return not_found('El contacto no existe.')

    def delete(self):
        with MongoDBHandler('contacts') as db:
            contact = db.extract(
                {'_id': ObjectId(self.id)}) if objectid_validation(self.id) else None
            if contact:
                db.delete({'_id': ObjectId(self.id)})
                return ok('Contacto eliminado correctamente.')
            return not_found('El Contacto no existe.')
