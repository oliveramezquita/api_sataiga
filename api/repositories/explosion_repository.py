from api.repositories.base_repository import BaseRepository


class ExplosionRepository(BaseRepository):
    """Acceso a la colección 'explosion' en MongoDB."""
    COLLECTION = 'explosion'
