from bson import ObjectId
from decimal import Decimal
from api_sataiga.handlers.mongodb_handler import MongoDBHandler
from api.helpers.validations import objectid_validation


class BaseRepository:
    """
    Repositorio genérico para acceso a MongoDB.
    Implementa operaciones CRUD reutilizables.
    """

    COLLECTION: str = None

    def __init__(self):
        if not self.COLLECTION:
            raise ValueError("La subclase debe definir la colección MongoDB.")
        self.db_handler = MongoDBHandler(self.COLLECTION)

    def find_all(self, query=None, order_field=None, order=1, projection=None):
        """Obtiene todos los documentos según un filtro opcional."""
        with self.db_handler as db:
            return db.extract(query=query, order_field=order_field, order=order, projection=projection)

    def find_by_id(self, _id: str):
        """Obtiene un documento por su ObjectId."""
        if not objectid_validation(_id):
            return None
        with self.db_handler as db:
            result = db.extract({'_id': ObjectId(_id)})
            return result[0] if result else None

    def insert(self, data: dict):
        """Inserta un nuevo documento."""
        with self.db_handler as db:
            return db.insert(data)

    def update(self, _id: str, update_data: dict, upsert: bool = False):
        """
        Realiza una actualización de documento en MongoDB.
        Acepta directamente operadores ($set, $push, $inc, etc.)
        o documentos simples. NO agrega $set automáticamente.
        """
        if not objectid_validation(_id):
            return None

        with self.db_handler as db:
            return db.update({'_id': ObjectId(_id)}, update_data, upsert=upsert)

    def delete(self, _id: str):
        """Elimina un documento existente."""
        if not objectid_validation(_id):
            return 0
        with self.db_handler as db:
            return db.delete({'_id': ObjectId(_id)})
