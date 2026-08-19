from api.repositories.base_repository import BaseRepository


class CustomerRepository(BaseRepository):
    """Acceso a la colección 'customers'."""
    COLLECTION = 'customers'
