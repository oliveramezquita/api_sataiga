from typing import Any, Dict
from api.services.base_service import BaseService
from api.repositories.client_repository import ClientRepository
from api.repositories.home_production_repository import HomeProductionRepository
from api.serializers.home_production_serializer import HomeProductionSerializer


class HomeProductionService(BaseService):
    """Lógica de negocio para home_production."""

    CACHE_PREFIX = "home_production"

    def __init__(self):
        self.client_repo = ClientRepository()
        self.hp_repo = HomeProductionRepository()

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
