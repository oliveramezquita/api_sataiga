from api.helpers.http_responses import created, ok, ok_paginated, not_found, bad_request
from api.services.employee_service import EmployeeService
from api.utils.pagination_utils import DummyPaginator, DummyPage
from api.helpers.get_query_params import get_query_params


class EmployeeUseCase:
    """Orquesta peticiones HTTP para el módulo de Empleados/Colaboradores."""

    def __init__(self, request=None, **kwargs):
        params = get_query_params(request)
        self.page = params["page"]
        self.page_size = params["page_size"]
        self.status = params.get("status")
        self.q = params["q"]
        self.data = kwargs.get('data')
        self.id = kwargs.get('id')
        self.service = EmployeeService()

    def save(self):
        try:
            self.service.create(self.data)
            return created(f'Empleado/Colaborador: {self.data['name']} creado exitosamente.')
        except ValueError as e:
            return bad_request(str(e))
        except LookupError as e:
            return bad_request(str(e))
        except Exception as e:
            return bad_request(f'Error inesperado: {e}')

    def get(self):
        """Método especial con paginación manual."""
        try:
            result = self.service.get_paginated(
                self.status, self.q, self.page, self.page_size
            )

            dummy_paginator = DummyPaginator(
                result["count"], result["total_pages"])
            dummy_page = DummyPage(
                result["current_page"], dummy_paginator, result["results"])
            return ok_paginated(dummy_paginator, dummy_page, result["results"])
        except Exception as e:
            return bad_request(f"Error al obtener los clientes: {e}")

    def update(self):
        try:
            self.service.update(self.id, self.data)
            return ok('El empleado/colaborador ha sido actualizado correctamente.')
        except LookupError as e:
            return not_found(str(e))
        except Exception as e:
            return bad_request(f'Error inesperado: {e}')

    def delete(self):
        try:
            self.service.delete(self.id)
            return ok('Empleado/colaborador eliminado correctamente.')
        except LookupError as e:
            return not_found(str(e))
        except Exception as e:
            return bad_request(f'Error inesperado: {e}')
