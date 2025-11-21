from api.repositories.base_repository import BaseRepository


class ContactRepository(BaseRepository):
    """Acceso a la colección 'contacts' en MongoDB."""
    COLLECTION = 'contacts'
