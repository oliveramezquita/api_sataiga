from api.repositories.base_repository import BaseRepository


class EmployeeRepository(BaseRepository):
    """Acceso a la colección 'employees' en MongoDB."""
    COLLECTION = 'employees'
