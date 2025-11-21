from api.repositories.base_repository import BaseRepository


class CatalogRepository(BaseRepository):
    """Acceso a la colección 'catalogs' en MongoDB."""
    COLLECTION = 'catalogs'
