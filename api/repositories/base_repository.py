from bson import ObjectId
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

    def find_by_id(self, _id: str, filters: dict = None):
        if not objectid_validation(_id):
            return None
        query = {'_id': ObjectId(_id)}
        if filters and isinstance(filters, dict):
            query.update(filters)
        with self.db_handler as db:
            result = db.extract(query)
            return result[0] if result else None

    def find_one(self, query=None, projection=None):
        with self.db_handler as db:
            result = db.extract(query=query, projection=projection)
            return result[0] if result else None

    def find_by_ids(self, ids: list[str], filters: dict = None, projection=None):
        valid_ids = [ObjectId(_id) for _id in ids if objectid_validation(_id)]
        if not valid_ids:
            return []

        query = {'_id': {'$in': valid_ids}}
        if filters and isinstance(filters, dict):
            query.update(filters)

        with self.db_handler as db:
            return db.extract(query=query, projection=projection)

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

    def delete_by_query(self, query: dict):
        """
        Elimina documentos usando un filtro/query personalizado.
        Ejemplo:
            repo.delete_by_query({"status": "inactive"})
        """
        if not isinstance(query, dict) or not query:
            raise ValueError("query debe ser un dict no vacío.")

        with self.db_handler as db:
            return db.delete(query)

    def update_one(self, query: dict, update_data: dict, upsert: bool = False):
        if not isinstance(query, dict) or not query:
            raise ValueError("query debe ser un dict no vacío.")
        with self.db_handler as db:
            return db.update(query, update_data, upsert=upsert)

    def upsert_one(self, query: dict, set_data: dict):
        # Siempre $set para evitar reemplazos accidentales
        return self.update_one(query, {"$set": set_data}, upsert=True)
