from bson import ObjectId
from api_sataiga.handlers.mongodb_handler import MongoDBHandler
from api.helpers.validations import objectid_validation


class ClientRepository:
    """Acceso a la colección 'clients'."""
    COLLECTION = 'clients'

    def find_valid_client(self, client_id: str):
        if not objectid_validation(client_id):
            return None
        with MongoDBHandler(self.COLLECTION) as db:
            clients = db.find(db, self.COLLECTION, {
                              '_id': ObjectId(client_id), 'type': 'PE'})
            return clients[0] if clients else None

    def find_pe_clients(self, query: str = None):
        """Obtiene clientes tipo 'PE' (Project Especial) con búsqueda opcional."""
        filters = {'type': 'PE'}
        if query:
            filters['$or'] = [
                {'name': {'$regex': query, '$options': 'i'}},
                {'address': {'$regex': query, '$options': 'i'}},
                {'email': {'$regex': query, '$options': 'i'}},
            ]
        with MongoDBHandler(self.COLLECTION) as db:
            # Usa extract ordenado por 'pe_id' (como tu versión original)
            clients = db.extract(filters, 'pe_id')
        return clients
