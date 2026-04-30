from api.repositories.base_repository import BaseRepository


class NotificationRepository(BaseRepository):
    """Acceso a la colección 'notifications' en MongoDB."""
    COLLECTION = 'notifications'
