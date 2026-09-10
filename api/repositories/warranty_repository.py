from api.repositories.base_repository import BaseRepository


class WarrantyRepository(BaseRepository):
    """Acceso a la colección 'warranties'."""
    COLLECTION = 'warranties'
