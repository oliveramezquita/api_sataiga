from api.repositories.base_repository import BaseRepository


class PrototypeRepository(BaseRepository):
    """Acceso a la colección 'prototypes' en MongoDB."""
    COLLECTION = 'prototypes'
