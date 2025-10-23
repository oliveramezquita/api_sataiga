from rest_framework import views
from rest_framework.request import Request
from rest_framework.response import Response
from api.use_cases.employee_use_case import EmployeeUseCase
from api.middlewares import BellartiAuthenticationMiddleware
import logging

logger = logging.getLogger(__name__)


class EmployeesView(views.APIView):
    """
    Endpoint para crear y listar empleados/colaboradores.

    Métodos:
        POST: Crea un nuevo empleado/colaborador.
        GET: Lista de empleados/colaboradores con paginación (page, itemsPerPage).
    """
    authentication_classes = [BellartiAuthenticationMiddleware]

    def post(self, request: Request) -> Response:
        """Crea un nuevo empleado/colaborador."""
        logger.debug("POST /employees recibido con datos: %s", request.data)
        use_case = EmployeeUseCase(data=request.data)
        response = use_case.save()
        logger.debug("Respuesta POST /employees: %s",
                     response.data if hasattr(response, 'data') else response)
        return response

    def get(self, request: Request) -> Response:
        """Obtiene la lista paginada de empleados/colaboradores."""
        logger.debug("GET /employees con params: %s", request.query_params)
        use_case = EmployeeUseCase(request=request)
        response = use_case.get()
        logger.debug("Respuesta GET /employees: %s",
                     response.data if hasattr(response, 'data') else response)
        return response


class EmployeeByIdView(views.APIView):
    """
    Endpoint para operaciones sobre un empleado/colaborador.

    Métodos:
        GET: Obtiene los detalles del empleado/colaborador.
        PATCH: Actualiza datos de un empleado/colaborador existente.
        DELETE: Elimina un empleado/colaborador.
    """
    authentication_classes = [BellartiAuthenticationMiddleware]

    def patch(self, request: Request, id: str) -> Response:
        """Actualiza un empleado/colaborador por su ID."""
        logger.debug("PATCH /employee/%s con datos: %s", id, request.data)
        use_case = EmployeeUseCase(data=request.data, id=id)
        return use_case.update()

    def delete(self, request: Request, id: str) -> Response:
        """Elimina un empleado/colaborador por su ID."""
        logger.debug("DELETE /employee/%s", id)
        use_case = EmployeeUseCase(id=id)
        return use_case.delete()
