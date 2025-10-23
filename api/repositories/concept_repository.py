from api.repositories.base_repository import BaseRepository


class ConceptRepository(BaseRepository):
    """Acceso a la colección 'concepts' en MongoDB."""
    COLLECTION = 'concepts'
