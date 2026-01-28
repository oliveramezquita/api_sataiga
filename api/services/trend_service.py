from typing import Optional, Dict, Any, Mapping, List
from api.services.base_service import BaseService
from api.repositories.client_repository import ClientRepository
from api.repositories.trend_repository import TrendRepository
from api.serializers.trend_serializer import TrendSerializer
from api.constants import TRENDS_FIELD_BY_TYPE


class TrendService(BaseService):
    """Lógica de negocio para tendencias."""

    CACHE_PREFIX = "trends"

    def __init__(self):
        self.client_repo = ClientRepository()
        self.trend_repo = TrendRepository()

    # ----------------------------------------------------------
    # CREAR TENDENCIA
    # ----------------------------------------------------------
    def create(self, data: Dict[str, Any]):
        """
        Crea una tendencia asociado a un cliente existente y un frente.
        Valida que el cliente exista por su ID.
        """
        client_id = data.get("client_id")
        client = self.client_repo.find_by_id(client_id)
        if not client:
            raise LookupError("El client no existe.")

        self._create(
            repo=self.trend_repo,
            data=data,
            required_fields=["client_id", "front"],
            cache_prefix=self.CACHE_PREFIX
        )

    # ----------------------------------------------------------
    # AGREGAR ELEMENTOS (MELAMINAS/GRANITOS)
    # ----------------------------------------------------------
    def add_items(self, trend_id: str, data: Dict[str, Any]):
        """Agrega los elementos (melaminas/granitos) a la tendencia."""
        self._validate_fields(
            data, ["client_id", "front", "item_type", "items"])

        client_id = data["client_id"]
        item_type = data["item_type"]
        raw_items = data["items"]

        # Validar item_type permitido
        if item_type not in TRENDS_FIELD_BY_TYPE:
            raise ValueError(
                "item_type inválido. Usa 'melamines' o 'granites'.")

        # Validar items sea lista no vacía
        if not isinstance(raw_items, list) or not raw_items:
            raise ValueError(
                "items debe ser una lista con al menos un elemento.")

        # Validar cliente
        client = self.client_repo.find_by_id(client_id, {"type": "VS"})
        if not client:
            raise LookupError(
                "El cliente seleccionado no existe o no es válido.")

        # TODO: Validar el frente (data["front"])

        # Validar cada item
        cleaned_items: List[Dict[str, Any]] = []
        for idx, item in enumerate(raw_items):
            if not isinstance(item, Mapping):
                raise ValueError(f"items[{idx}] debe ser un objeto.")

            self._validate_fields(item, ["id", "name", "percentage"])

            item_id = item.get("id")
            name = item.get("name")
            percentage = item.get("percentage")

            if name is None or (isinstance(name, str) and not name.strip()):
                raise ValueError(f"items[{idx}].name no puede ser null/vacío.")

            try:
                percentage_num = float(percentage)
            except (TypeError, ValueError):
                raise ValueError(f"items[{idx}].percentage debe ser numérico.")

            if percentage_num <= 0:
                raise ValueError(
                    f"items[{idx}].percentage debe ser mayor a cero.")

            cleaned_items.append(
                {"id": item_id, "name": name, "percentage": percentage_num})

        field_name = TRENDS_FIELD_BY_TYPE[item_type]

        # Actualizar SOLO el campo correspondiente
        self._update(
            repo=self.trend_repo,
            _id=trend_id,
            data={field_name: cleaned_items},
            cache_prefix=self.CACHE_PREFIX,
        )

    # ----------------------------------------------------------
    # LISTADO (con cache por filtro)
    # ----------------------------------------------------------

    def get(self, client_id: Optional[str] = None, front: Optional[str] = None):
        """
        Lista de tendencias aplicando filtros del cliente y frente como opcional.
        """
        filters = {k: v for k, v in {
            'client_id': client_id,
            'front': front,
        }.items() if v is not None}

        trends = self._get_all_cached(
            repo=self.trend_repo,
            filters=filters,
            prefix=self.CACHE_PREFIX,
        )
        return TrendSerializer(trends, many=True).data

    def get_by_id(self, client_id: str):
        return self._get_by_id(
            self.trend_repo, client_id, serializer=TrendSerializer
        )

    # ----------------------------------------------------------
    # ELIMINAR TENDENCIA
    # ----------------------------------------------------------

    def delete(self, trend_id: str):
        self._delete(
            repo=self.trend_repo,
            _id=trend_id,
            cache_prefix=self.CACHE_PREFIX,
        )
