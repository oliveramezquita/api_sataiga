from typing import Any, Dict
from rest_framework.exceptions import ValidationError
from api.services.base_service import BaseService
from api.repositories.client_repository import ClientRepository
from api.repositories.home_production_repository import HomeProductionRepository
from api.repositories.lot_repository import LotRepository
from api.repositories.explosion_repository import ExplosionRepository
from api.serializers.home_production_serializer import HomeProductionSerializer


class HomeProductionService(BaseService):
    """Lógica de negocio para home_production."""

    CACHE_PREFIX = "home_production"

    def __init__(self):
        self.client_repo = ClientRepository()
        self.hp_repo = HomeProductionRepository()
        self.lot_repo = LotRepository()
        self.exp_repo = ExplosionRepository()

    def create(self, data: Dict[str, Any]):
        client_id = data.get("client_id")
        client = self.client_repo.find_by_id(client_id)
        if not client:
            raise LookupError("El client no existe.")

        self._create(
            repo=self.hp_repo,
            data={**data,
                  'lots': {},
                  'progress': 0,
                  'status': 0},
            required_fields=["client_id", "front", "od"],
            cache_prefix=self.CACHE_PREFIX
        )

    def get_paginated(self, filters: dict, page: int, page_size: int, sort_by: str = None, order_by: int = 1):
        items = self._get_all_cached(
            self.hp_repo,
            filters,
            prefix=self.CACHE_PREFIX,
            order_field=sort_by,
            order=order_by
        )
        return self._paginate(items, page, page_size, serializer=HomeProductionSerializer)

    def get_by_id(self, hp_id: str):
        return self._get_by_id(self.hp_repo, hp_id, serializer=HomeProductionSerializer)

    def update(self, hp_id: str, data: Dict[str, Any]) -> str:
        if not hp_id:
            raise ValidationError("home_production_id es requerido.")
        if not data:
            raise ValidationError(
                "Se requieren datos para actualizar la OD.")
        self._update(
            repo=self.hp_repo,
            _id=hp_id,
            data=data,
            cache_prefix=self.CACHE_PREFIX,
        )
        return 'OD actualizada correctamente.'

    def delete(self, hp_id: str) -> str:
        if not hp_id:
            raise ValidationError("home_production_id es requerido.")
        hp = self._get_by_id(self.hp_repo, _id=hp_id)
        if not hp:
            raise LookupError("La OD noexiste.")
        self._delete(
            repo=self.hp_repo,
            _id=hp_id,
            cache_prefix=self.CACHE_PREFIX
        )
        hp_query = {'home_production_id': hp_id}
        self._delete_by_query(self.lot_repo, hp_query)
        self._delete_by_query(self.exp_repo, hp_query)
        return 'OD eliminada correctamente.'
