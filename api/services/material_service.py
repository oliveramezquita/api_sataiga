from api.services.base_service import BaseService
from api.repositories.material_repository import MaterialRepository
from api.serializers.material_serializer import MaterialSerializer


class MaterialService(BaseService):
    CACHE_PREFIX = "materials"

    def __init__(self):
        self.material_repo = MaterialRepository()

    def get(self, filters: dict, sort_by: str = 'concept', order_by: int = 1):
        items = self._get_all_cached(
            self.material_repo,
            filters,
            prefix=self.CACHE_PREFIX,
            order_field=sort_by,
            order=order_by
        )

        return MaterialSerializer(items, many=True).data

    def get_paginated(self, filters: dict, page: int, page_size: int, sort_by: str = 'concept', order_by: int = 1):
        items = self._get_all_cached(
            self.material_repo,
            filters,
            prefix=self.CACHE_PREFIX,
            order_field=sort_by,
            order=order_by
        )
        return self._paginate(items, page, page_size, serializer=MaterialSerializer)
