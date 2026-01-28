from api.repositories.base_repository import BaseRepository
from api.helpers.validations import objectid_validation
from bson import ObjectId


class MaterialRepository(BaseRepository):
    """Acceso a la colección 'materials' en MongoDB."""
    COLLECTION = 'materials'

    def find_many_by_ids(self, ids: list[str]):
        # Si viene vacío, regresamos vacío (tu servicio ya lo maneja)
        if not ids:
            return []

        # Filtrar ids inválidos para evitar exceptions de ObjectId(...)
        valid_ids = [x for x in ids if objectid_validation(x)]
        if not valid_ids:
            return []

        object_ids = [ObjectId(x) for x in valid_ids]

        with self.db_handler as db:
            return db.extract(query={"_id": {"$in": object_ids}})
