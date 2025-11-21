from api.repositories.base_repository import BaseRepository


class MaterialRepository(BaseRepository):
    """Acceso a la colección 'materials' en MongoDB."""
    COLLECTION = 'materials'
