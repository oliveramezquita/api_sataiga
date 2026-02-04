from typing import Any, Iterable, Optional
from bson import ObjectId

from api.repositories.base_repository import BaseRepository
from api.helpers.validations import objectid_validation


class MaterialRepository(BaseRepository):
    """Acceso a la colección 'materials' en MongoDB."""
    COLLECTION = "materials"

    def find_many_by_ids(
        self,
        ids: Iterable[Any],
        projection: Optional[dict] = None,
        dedupe: bool = True,
    ):
        """
        Obtiene materiales por lista de ids (str u ObjectId).
        - Filtra ids inválidos para evitar exceptions
        - Permite projection para optimizar performance
        - dedupe=True elimina ids repetidos antes del query
        """
        if not ids:
            return []

        object_ids: list[ObjectId] = []
        for x in ids:
            if isinstance(x, ObjectId):
                object_ids.append(x)
            elif isinstance(x, str) and objectid_validation(x):
                object_ids.append(ObjectId(x))

        if not object_ids:
            return []

        if dedupe:
            # Quitar duplicados manteniendo el orden
            seen = set()
            unique_ids = []
            for oid in object_ids:
                if oid not in seen:
                    seen.add(oid)
                    unique_ids.append(oid)
            object_ids = unique_ids

        with self.db_handler as db:
            return db.extract(
                query={"_id": {"$in": object_ids}},
                projection=projection,
            )
