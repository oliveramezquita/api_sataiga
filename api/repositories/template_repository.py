from api.repositories.base_repository import BaseRepository


class TemplateRepository(BaseRepository):
    """Acceso a la colección 'templates' en MongoDB."""
    COLLECTION = 'templates'
