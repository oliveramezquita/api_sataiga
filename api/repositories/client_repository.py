from api.repositories.base_repository import BaseRepository


class ClientRepository(BaseRepository):
    """Acceso a la colección 'clients'."""
    COLLECTION = 'clients'
