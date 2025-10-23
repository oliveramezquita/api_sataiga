from api.repositories.base_repository import BaseRepository


class ProjectRepository(BaseRepository):
    """Acceso a la colección 'projects' en MongoDB."""
    COLLECTION = 'projects'
