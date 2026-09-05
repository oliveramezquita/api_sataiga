from api.repositories.base_repository import BaseRepository


class AuthRepository(BaseRepository):
    """Acceso a la colección 'auth'."""
    COLLECTION = 'auth'
