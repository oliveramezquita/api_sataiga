from typing import Optional
from api.services.base_service import BaseService
from api.repositories.client_repository import ClientRepository
from api.serializers.client_serializer import ClientSerializer


class ClientService(BaseService):
    """Lógica de negocio pura para Empleados y Colaboradores."""

    CACHE_PREFIX = "clients"

    def __init__(self):
        self.client_repo = ClientRepository()

    def create(self, data: dict):
        def preprocess(data):
            if data.get("type") == "PE":
                data["pe_id"] = self.__create_consecutive()
            return data

        self._create(
            repo=self.client_repo,
            data=data,
            required_fields=["type", "name"],
            cache_prefix=self.CACHE_PREFIX,
            preprocess=preprocess,
        )

    def get_paginated(self, client_type: str, q: Optional[str], page: int, page_size: int, sort_by: str = None, order_by: int = 1):
        filters = {"type": client_type}
        if q:
            filters["$or"] = [
                {"name": {"$regex": q, "$options": "i"}},
                {"email": {"$regex": q, "$options": "i"}},
            ]
        items = self._get_all_cached(
            self.client_repo, filters,
            prefix=self.CACHE_PREFIX,
            order_field=sort_by,
            order=order_by)
        return self._paginate(items, page, page_size, serializer=ClientSerializer)

    def get_by_id(self, client_id: str):
        return self._get_by_id(self.client_repo, client_id, serializer=ClientSerializer)

    def update(self, client_id: str, data: dict):
        self._update(self.client_repo, client_id, data,
                     cache_prefix=self.CACHE_PREFIX)

    def delete(self, client_id: str):
        self._delete(self.client_repo, client_id,
                     cache_prefix=self.CACHE_PREFIX)

    def __create_consecutive(self) -> int:
        clients = self.client_repo.find_all({"type": "PE"})
        if not clients:
            return 1
        last = max(clients, key=lambda c: c.get("pe_id", 0))
        return int(last["pe_id"]) + 1
