from api.repositories.base_repository import BaseRepository


class VolumetryRepository(BaseRepository):
    """Acceso a la colección 'volumetries' en MongoDB."""
    COLLECTION = 'volumetries'
