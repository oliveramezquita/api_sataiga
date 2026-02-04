from api.repositories.base_repository import BaseRepository


class QuantificationRepository(BaseRepository):
    """Acceso a la colección 'quantification' en MongoDB."""
    COLLECTION = 'quantification'
