from bson import ObjectId
from typing import Dict, Any, List, Union
from api.utils.cache_utils import invalidate_cache
from api.repositories.catalog_repository import CatalogRepository
from api.serializers.catalog_serializer import CatalogSerializer
from api.services.base_service import BaseService


class CatalogValidationError(Exception):
    pass


class CatalogService(BaseService):
    """
    Lógica de negocio para catálogos, reutilizando CatalogRepository.
    Hereda de BaseService para centralizar operaciones CRUD y cache.
    """

    CACHE_PREFIX = "catalogs"

    def __init__(self):
        self.catalog_repo = CatalogRepository()

    def get_by_name(self, name: str, order_by: str = "asc"):
        docs = self._get_all_cached(
            self.catalog_repo,
            {'name': name},
            prefix='catalog'
        )
        if not docs:
            raise LookupError(f"El catálogo '{name}' no existe.")

        doc = docs[0]
        doc["values"] = self._sort_values(doc.get("values"), order_by)
        return CatalogSerializer(doc).data

    def get_all(self, order_by: str = "asc"):
        catalogs = self._get_all_cached(
            repo=self.catalog_repo,
            prefix=self.CACHE_PREFIX
        )
        if not catalogs:
            return []

        for doc in catalogs:
            doc["values"] = self._sort_values(doc.get("values"), order_by)

        return CatalogSerializer(catalogs, many=True).data

    def get_by_id(self, catalog_id: str):
        """Obtiene un catálogo por ID (usa método genérico del BaseService)."""
        return self._get_by_id(self.catalog_repo, catalog_id, serializer=CatalogSerializer)

    # ----------------------------------------------------------
    # CREAR / ACTUALIZAR / ELIMINAR (con base genérica)
    # ----------------------------------------------------------
    def create(self, data: Dict[str, Any]) -> Dict[str, str]:
        """
        Crea un catálogo:
        - Normaliza 'values'
        - Valida estructura
        - Inserta y limpia cache
        """
        payload = self._normalize_payload(data)
        self._validate_payload(payload)

        inserted_id = self._create(
            repo=self.catalog_repo,
            data=payload,
            required_fields=["name", "values"],
            cache_prefix=self.CACHE_PREFIX,
        )

        # invalidar también cache individual
        invalidate_cache("catalog")

        return {"id": str(inserted_id)}

    def update(self, catalog_id: str, data: Dict[str, Any]) -> str:
        """
        Actualiza un catálogo existente validando ID y estructura.
        """
        if not ObjectId.is_valid(catalog_id):
            raise CatalogValidationError("ID de catálogo inválido.")

        payload = self._normalize_payload(data)
        self._validate_payload(payload)

        self._update(
            repo=self.catalog_repo,
            _id=catalog_id,
            data=payload,
            cache_prefix=self.CACHE_PREFIX,
        )

        # invalidar también cache individual
        invalidate_cache("catalog")

    def delete(self, catalog_id: str) -> str:
        """
        Elimina un catálogo validando ID.
        """
        if not ObjectId.is_valid(catalog_id):
            raise CatalogValidationError("ID de catálogo inválido.")

        self._delete(
            repo=self.catalog_repo,
            _id=catalog_id,
            cache_prefix=self.CACHE_PREFIX,
        )

        # invalidar también cache individual
        invalidate_cache("catalog")

    # ----------------------------------------------------------
    # Helpers internos
    # ----------------------------------------------------------
    def _validate_payload(self, payload: Dict[str, Any]) -> None:
        required = ['name', 'values']
        if not all(k in payload for k in required):
            raise CatalogValidationError(
                "Faltan campos requeridos: 'name' y/o 'values'.")

        values = payload.get('values')

        if isinstance(values, list) and len(values) == 0:
            raise CatalogValidationError(
                "Inserte al menos un elemento en 'values'.")

        if isinstance(values, dict):
            if not any(isinstance(v, list) and len(v) > 0 for v in values.values()):
                raise CatalogValidationError(
                    "Inserte al menos un elemento en 'values' (dict).")

    def _normalize_payload(self, data: Dict[str, Any]) -> Dict[str, Any]:
        payload = dict(data)
        values = payload.get('values')

        if isinstance(values, list):
            payload['values'] = [x for x in values if x]

        elif isinstance(values, dict):
            cleaned: Dict[str, List[Any]] = {}
            for key, arr in values.items():
                if isinstance(arr, list):
                    cleaned_arr = [x for x in arr if x]
                else:
                    cleaned_arr = [arr] if arr else []
                cleaned[key] = cleaned_arr
            payload['values'] = cleaned

        return payload

    def _sort_values(self, values: Union[List[Any], Dict[str, List[Any]]], order_by: str):
        reverse = (order_by == "desc")

        if isinstance(values, list):
            return sorted(values, reverse=reverse)

        if isinstance(values, dict):
            return {
                key: sorted(values[key], reverse=reverse)
                for key in sorted(values.keys(), reverse=reverse)
            }

        return values

    # ----------------------------------------------------------
    # ACTUALIZACIÓN EXTERNA (usada por otros módulos)
    # ----------------------------------------------------------
    @staticmethod
    def external_update(name: str, new_value: Any) -> None:
        """
        Permite que otros módulos actualicen los valores de un catálogo
        sin duplicar lógica ni crear instancias del servicio.

        - Si el catálogo no existe, no hace nada.
        - Si `new_value` es un dict, actualiza claves existentes o las agrega.
        - Si `new_value` es un str, lo agrega al arreglo principal.
        - Evita duplicados.
        """
        from api.repositories.catalog_repository import CatalogRepository
        from api.utils.cache_utils import invalidate_cache

        repo = CatalogRepository()
        docs = repo.find_all({"name": name})
        if not docs:
            return  # No existe el catálogo, no se hace nada

        catalog = docs[0]
        values = catalog.get("values", [])

        # --- Si el catálogo tiene estructura tipo dict ---
        if isinstance(values, dict):
            if not isinstance(new_value, dict):
                raise ValueError(
                    "El nuevo valor debe ser un dict para catálogos con estructura dict."
                )

            for key, val in new_value.items():
                if key in values:
                    # Añadir valor evitando duplicados
                    if val not in values[key]:
                        values[key].append(val)
                else:
                    # Nueva clave
                    values[key] = [val]

        # --- Si el catálogo tiene estructura tipo lista ---
        elif isinstance(values, list):
            if isinstance(new_value, str):
                if new_value not in values:
                    values.append(new_value)
            else:
                raise ValueError(
                    "El nuevo valor debe ser una cadena para catálogos tipo lista."
                )

        # --- Guardar cambios ---
        repo.update(str(catalog["_id"]), {"values": values})

        # --- Invalidar caché ---
        invalidate_cache("catalog")
        invalidate_cache("catalogs")
