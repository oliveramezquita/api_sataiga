from typing import Optional, Dict, Any
from api.repositories.employee_repository import EmployeeRepository
from api.serializers.employee_serializer import EmployeeSerializer
from api.services.base_service import BaseService


class EmployeeService(BaseService):
    """Lógica de negocio pura para Empleados y Colaboradores."""

    CACHE_PREFIX = "employees"

    def __init__(self):
        self.employee_repo = EmployeeRepository()

    # ----------------------------------------------------------
    # CREAR EMPLEADO
    # ----------------------------------------------------------
    def create(self, data: Dict[str, Any]) -> Dict[str, str]:
        """
        Crea un nuevo empleado o colaborador.
        Valida campos requeridos y asigna estado activo por defecto.
        Invalida la caché global de empleados.
        """
        # Validar campos requeridos (heredado del BaseService)
        self._validate_fields(data, ["name", "number", "activity"])

        # Insertar con status=True
        data_with_status = {**data, "status": True}

        inserted_id = self._create(
            repo=self.employee_repo,
            data=data_with_status,
            required_fields=["name", "number", "activity"],
            cache_prefix=self.CACHE_PREFIX,
        )

        return {"id": str(inserted_id)}

    # ----------------------------------------------------------
    # OBTENER EMPLEADOS PAGINADOS (CON CACHE)
    # ----------------------------------------------------------
    def get_paginated(self, status: Optional[str], q: Optional[str], page: int, page_size: int):
        """
        Devuelve los empleados filtrados por estado o búsqueda (q),
        con paginación y cache de resultados.
        """
        filters: Dict[str, Any] = {}
        if status is not None:
            filters["status"] = status
        if q:
            filters["$or"] = [
                {"number": {"$regex": q, "$options": "i"}},
                {"name": {"$regex": q, "$options": "i"}},
                {"activity": {"$regex": q, "$options": "i"}},
            ]

        items = self._get_all_cached(
            self.employee_repo, filters, prefix=self.CACHE_PREFIX)
        return self._paginate(items, page, page_size, serializer=EmployeeSerializer)

    # ----------------------------------------------------------
    # OBTENER POR ID
    # ----------------------------------------------------------
    def get_by_id(self, employee_id: str):
        """
        Obtiene un empleado por su ID, usando el método genérico del BaseService.
        Lanza LookupError si no existe.
        """
        return self._get_by_id(self.employee_repo, employee_id, serializer=EmployeeSerializer)

    # ----------------------------------------------------------
    # ACTUALIZAR EMPLEADO
    # ----------------------------------------------------------
    def update(self, employee_id: str, data: Dict[str, Any]) -> str:
        """
        Actualiza la información de un empleado existente.
        Lanza LookupError si no existe.
        Invalida la caché global de empleados.
        """
        self._update(
            repo=self.employee_repo,
            _id=employee_id,
            data=data,
            cache_prefix=self.CACHE_PREFIX,
        )
        return "El empleado/colaborador ha sido actualizado correctamente."

    # ----------------------------------------------------------
    # ELIMINAR EMPLEADO
    # ----------------------------------------------------------
    def delete(self, employee_id: str) -> str:
        """
        Elimina un empleado existente.
        Lanza LookupError si no existe.
        Invalida la caché global de empleados.
        """
        self._delete(
            repo=self.employee_repo,
            _id=employee_id,
            cache_prefix=self.CACHE_PREFIX,
        )
        return "Empleado/colaborador eliminado correctamente."
