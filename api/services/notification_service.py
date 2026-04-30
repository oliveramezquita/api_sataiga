from api.serializers.notification_serializer import NotificationSerializer
from api.services.base_service import BaseService
from api.repositories.notification_repository import NotificationRepository


class NotificationService(BaseService):
    """Lógica de negocio para las Notificaciones."""

    CACHE_PREFIX = "notifications"

    def __init__(self):
        self.notification_repository = NotificationRepository()

    def get_paginated(self, filters: dict, page: int, page_size: int, sort_by: str = 'created_at', order_by: int = 1):
        items = self._get_all_cached(
            self.notification_repository,
            filters,
            prefix=self.CACHE_PREFIX,
            order_field=sort_by,
            order=order_by
        )

        return self._paginate(items, page, page_size, serializer=NotificationSerializer)
