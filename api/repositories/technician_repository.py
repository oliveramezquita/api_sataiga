from api.repositories.base_repository import BaseRepository


class TechnicianRepository(BaseRepository):
    """Acceso a la colección 'technicians'."""
    COLLECTION = 'technicians'
