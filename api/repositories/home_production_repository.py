from api.repositories.base_repository import BaseRepository


class HomeProductionRepository(BaseRepository):
    """Acceso a la colección 'home_production' en MongoDB."""
    COLLECTION = 'home_production'
