from api.repositories.employee_repository import EmployeeRepository


class EmployeeService:
    """Lógica de negocio pura para Empleados y Colaboradores."""

    def __init__(self):
        self.employee_repo = EmployeeRepository()

    def _validate_fields(self, data: dict, required_fields: list[str]):
        missing = [f for f in required_fields if not data.get(f)]
        if missing:
            raise ValueError(
                f'Campos requeridos faltantes: {", ".join(missing)}')

    def create(self, data: dict) -> None:
        self._validate_fields(data, ['name', 'number', 'activity'])
        _ = self.employee_repo.insert({**data, 'status': True})

    def get_all(self, query: dict):
        return self.employee_repo.find_all(query=query, order_field='created_at', order=-1)

    def get_by_id(self, employee_id: str):
        employee = self.employee_repo.find_by_id(employee_id)
        if not employee:
            raise LookupError('El empleado/colaborador no existe.')
        return employee

    def update(self, employee_id: str, data: dict):
        employee = self.employee_repo.find_by_id(employee_id)
        if not employee:
            raise LookupError('El empleado/colaborador no existe.')
        self.employee_repo.update(employee_id, data)

    def delete(self, employee_id: str):
        employee = self.employee_repo.find_by_id(employee_id)
        if not employee:
            raise LookupError('El empleado/colaborador no existe.')
        self.employee_repo.delete(employee_id)
