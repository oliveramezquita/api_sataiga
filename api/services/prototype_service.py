from typing import Optional, Dict, Any
from decimal import Decimal
from api.services.base_service import BaseService
from api.repositories.prototype_repository import PrototypeRepository
from api.repositories.client_repository import ClientRepository
from api.services.catalog_service import CatalogService
from api.serializers.prototype_serializer import PrototypeSerializer


class TendencyValidationError(Exception):
    """Error de validación de campos de catálogo o prototipo."""
    pass


class PrototypeService(BaseService):
    """
    Lógica de negocio para la colección 'prototypes'.
    - Usa cache por filtros.
    - Aplica paginación heredada del BaseService.
    - Valida porcentajes de 'tendencies'.
    - Valida cliente y duplicados antes de crear.
    """

    CACHE_PREFIX = "prototypes"

    def __init__(self):
        self.prototype_repo = PrototypeRepository()
        self.client_repo = ClientRepository()

    # ----------------------------------------------------------
    # CREAR PROTOTIPO (refactor del save del UseCase)
    # ----------------------------------------------------------
    def create(self, data: Dict[str, Any]) -> str:
        """
        Crea un nuevo prototipo validando:
        - Campos requeridos
        - Cliente válido (solo tipo VS)
        - No duplicado (client_id + name + front)
        - Actualiza catálogos relacionados
        """
        required_fields = ["client_id", "name", "front"]
        self._validate_fields(data, required_fields)

        client_id = data["client_id"]

        # 🔹 Validar cliente
        client = self.client_repo.find_by_id(client_id, {"type": "VS"})
        if not client:
            raise LookupError(
                "El cliente seleccionado no existe o no es válido.")

        # 🔹 Verificar duplicado
        existing = self.prototype_repo.find_all({
            "client_id": client_id,
            "name": data["name"],
            "front": data["front"],
        })
        if existing:
            raise ValueError("El prototipo ya existe.")

        # 🔹 Actualizar catálogos externos
        client_name = data.get("client_name")
        if client_name:
            CatalogService.external_update(
                "Frentes", {client_name: data["front"]})
            CatalogService.external_update(
                "Prototipos", {client_name: data["name"]})

        # 🔹 Ajustar nombre antes de guardar
        payload = {
            **data,
            "name": f"{data['name']} Cocina",
        }

        # 🔹 Insertar usando método genérico
        self._create(
            repo=self.prototype_repo,
            data=data,
            required_fields=required_fields,
            cache_prefix=self.CACHE_PREFIX,
        )

        # 🔹 Insertar usando método genérico (Cocina)
        self._create(
            repo=self.prototype_repo,
            data=payload,
            required_fields=required_fields,
            cache_prefix=self.CACHE_PREFIX,
        )

    # ----------------------------------------------------------
    # PAGINACIÓN SOBRE RESULTADOS CACHEADOS
    # ----------------------------------------------------------
    def get_paginated(
        self,
        q: Optional[str],
        page: int,
        page_size: int,
        sort_by: str = None,
        order_by: int = 1,
        client: Optional[str] = None,
        front: Optional[str] = None,
    ):
        filters = {}
        if client:
            filters["client_id"] = client
        if front:
            filters["front"] = front
        if q:
            filters["$or"] = [
                {"client_name": {"$regex": q, "$options": "i"}},
                {"name": {"$regex": q, "$options": "i"}},
                {"front": {"$regex": q, "$options": "i"}},
            ]

        items = self._get_all_cached(
            self.prototype_repo,
            filters,
            prefix=self.CACHE_PREFIX,
            order_field=sort_by,
            order=order_by
        )
        return self._paginate(items, page, page_size, serializer=PrototypeSerializer)

    def get_by_id(self, prototype_id: str):
        return self._get_by_id(
            self.prototype_repo, prototype_id, serializer=PrototypeSerializer
        )

    def update(self, prototype_id: str, data: Dict[str, Any]) -> str:
        prototype = self.prototype_repo.find_by_id(prototype_id)
        if not prototype:
            raise LookupError("El prototipo no existe.")

        if "tendencies" in data and data["tendencies"] is not None:
            self._validate_tendencies(data["tendencies"])

        self._update(
            repo=self.prototype_repo,
            _id=prototype_id,
            data=data,
            cache_prefix=self.CACHE_PREFIX,
        )

    def delete(self, prototype_id: str) -> str:
        self._delete(
            repo=self.prototype_repo,
            _id=prototype_id,
            cache_prefix=self.CACHE_PREFIX,
        )

    # ----------------------------------------------------------
    # VALIDACIÓN DE TENDENCIAS
    # ----------------------------------------------------------
    def _validate_tendencies(self, tendencies: list[Dict[str, Any]]):
        if not isinstance(tendencies, list):
            raise TendencyValidationError(
                "El campo 'tendencias' debe ser una lista.")

        try:
            total_percentage = sum(
                Decimal(str(t.get("percentage", 0))) for t in tendencies
            )
        except (TypeError, ValueError, ArithmeticError):
            raise TendencyValidationError(
                "Todos los campos 'porcentaje' deben ser numéricos."
            )

        if abs(total_percentage - 100) > Decimal("0.01"):
            raise TendencyValidationError(
                f"La suma de porcentajes debe ser 100. Actualmente es {total_percentage:.2f}."
            )
