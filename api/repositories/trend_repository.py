from api.repositories.base_repository import BaseRepository


class TrendRepository(BaseRepository):
    """Acceso a la colección 'trends' en MongoDB."""
    COLLECTION = 'trends'
