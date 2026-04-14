import math
from typing import Optional, Dict, Any, Mapping, List
from api.services.base_service import BaseService
from api.repositories.client_repository import ClientRepository
from api.repositories.trend_repository import TrendRepository
from api.serializers.trend_serializer import TrendSerializer
from api.constants import TRENDS_FIELD_BY_TYPE
from api.helpers.validations import parse_bool, float_validation


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

        # TODO(security): evaluar límite máximo de items para evitar abuso del endpoint (DoS lógico)
        # TODO (update): Validar el frente (data["front"])

        # Validar cliente
        client = self.client_repo.find_by_id(client_id, {"type": "VS"})
        if not client:
            raise LookupError(
                "El cliente seleccionado no existe o no es válido.")

        def parse_positive_float(value: Any, field: str, idx: int) -> float:
            try:
                n = float(value)
            except (TypeError, ValueError):
                raise ValueError(f"items[{idx}].{field} debe ser numérico.")
            if not math.isfinite(n):
                raise ValueError(
                    f"items[{idx}].{field} debe ser un número finito.")
            if n <= 0:
                raise ValueError(
                    f"items[{idx}].{field} debe ser mayor a cero.")
            return n

        cleaned_items: List[Dict[str, Any]] = []
        total_percent = 0.0

        for idx, item in enumerate(raw_items):
            if not isinstance(item, Mapping):
                raise ValueError(f"items[{idx}] debe ser un objeto.")

            # id no es relevante para el sistema, solo exigimos name y percentage
            self._validate_fields(item, ["name", "percentage"])

            item_id = item.get("id")
            name = item.get("name")

            if not isinstance(name, str) or not name.strip():
                raise ValueError(f"items[{idx}].name no puede ser null/vacío.")
            name = name.strip()

            bicolor = parse_bool(item.get("bicolor"))

            percentage = parse_positive_float(
                item.get("percentage"), "percentage", idx)

            # Evitar falsos > 100 por precisión float (tolerancia pequeña)
            total_percent += percentage
            if total_percent > 100.0 + 1e-9:
                raise ValueError(
                    f"items[{idx}] el total del porcentaje no debe ser mayor a 100%.")

            color_a = None
            color_b = None

            # Solo si es bicolor: validar A/B y su suma
            if bicolor is True:
                color_a = float_validation(item.get("color_a"), None)
                color_b = float_validation(item.get("color_b"), None)

                # Requeridos en bicolor
                if color_a is None or color_b is None:
                    raise ValueError(
                        f"items[{idx}] color_a y color_b son requeridos cuando bicolor es true.")

                # Validar numéricos, finitos y > 0 (usa la misma lógica)
                color_a = parse_positive_float(color_a, "color_a", idx)
                color_b = parse_positive_float(color_b, "color_b", idx)

                if (color_a + color_b) > 100.0 + 1e-9:
                    raise ValueError(
                        f"items[{idx}] la suma de los porcentajes bicolor no puede ser mayor a 100%."
                    )

            cleaned_items.append({
                "id": item_id,
                "name": name,
                "percentage": percentage,
                "bicolor": bicolor,
                "color_a": color_a,
                "color_b": color_b,
            })

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
