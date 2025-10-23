from django.core.paginator import Paginator
from api.helpers.http_responses import created, ok, ok_paginated, not_found, bad_request
from api.serializers.employee_serializer import EmployeeSerializer
from api.services.employee_service import EmployeeService
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
            _ = self.service.create(self.data)
            return created(f'Empleado/Colaborador: {self.data['name']} creado exitosamente.')
        except ValueError as e:
            return bad_request(str(e))
        except LookupError as e:
            return bad_request(str(e))
        except Exception as e:
            return bad_request(f'Error inesperado: {e}')

    def get(self):
        filters = {}
        if self.status is not None:
            filters['status'] = self.status
        if self.q:
            filters['$or'] = [
                {'number': {'$regex': self.q, '$options': 'i'}},
                {'name': {'$regex': self.q, '$options': 'i'}},
                {'activity': {'$regex': self.q, '$options': 'i'}},
            ]
        employees = self.service.get_all(filters)
        paginator = Paginator(employees, per_page=self.page_size)
        page = paginator.get_page(self.page)
        serialized = EmployeeSerializer(page.object_list, many=True).data
        return ok_paginated(paginator, page, serialized)

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
