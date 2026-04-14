from api.repositories.base_repository import BaseRepository


class LotRepository(BaseRepository):
    """Acceso a la colección 'lots' en MongoDB."""
    COLLECTION = 'lots'
