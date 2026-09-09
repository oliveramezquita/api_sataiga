from rest_framework import views
from rest_framework.request import Request
from rest_framework.response import Response
from api.use_cases.technician_use_case import TechnicianUseCase
from api.middlewares import BellartiAuthenticationMiddleware
import logging

logger = logging.getLogger(__name__)


class TechniciansView(views.APIView):
    """
    Endpoint para crear y listar técnicos de Postventa.

    Métodos:
        POST: Crea un nuevo técnico de Postventa.
        GET: Lista de técnicos con paginación (page, itemsPerPage).
    """
    authentication_classes = [BellartiAuthenticationMiddleware]

    def post(self, request: Request) -> Response:
        """Crea un nuevo técnico de Postventa."""
        logger.debug(
            "POST /after_sales/technicians recibido con datos: %s", request.data)
        use_case = TechnicianUseCase(data=request.data)
        response = use_case.save()
        logger.debug("Respuesta POST /after_sales/technicians: %s",
                     response.data if hasattr(response, 'data') else response)
        return response

    def get(self, request: Request) -> Response:
        """Obtiene la lista paginada de técnicos de Postventa."""
        logger.debug("GET /after_sales/technicians con params: %s",
                     request.query_params)
        use_case = TechnicianUseCase(request=request)
        response = use_case.get()
        logger.debug("Respuesta GET /after_sales/technicians: %s",
                     response.data if hasattr(response, 'data') else response)
        return response


class TechnicianByIdView(views.APIView):
    """
    Endpoint para operaciones sobre un técnico de Postventa en específico.

    Métodos:
        GET: Obtiene los detalles del técnico.
        PATCH: Actualiza datos de un técnico existente.
        DELETE: Elimina un técnico.
    """
    authentication_classes = [BellartiAuthenticationMiddleware]

    def get(self, request: Request, id: str) -> Response:
        """Obtiene un técnico de Postventa por su ID."""
        logger.debug("GET /after_sales/technician/%s", id)
        use_case = TechnicianUseCase(id=id)
        return use_case.get_by_id()

    def patch(self, request: Request, id: str) -> Response:
        """Actualiza un técnico de Postventa por su ID."""
        logger.debug(
            "PATCH /after_sales/technician/%s con datos: %s", id, request.data)
        use_case = TechnicianUseCase(data=request.data, id=id)
        return use_case.update()

    def delete(self, request: Request, id: str) -> Response:
        """Elimina un técnico de Postventa por su ID."""
        logger.debug("DELETE /after_sales/technician/%s", id)
        use_case = TechnicianUseCase(id=id)
        return use_case.delete()


class TechnicianStatusView(views.APIView):
    """
    Endpoint para operaciones sobre el estatus de un técnico de Postventa.

    Métodos:
        PATCH: Actualiza el estatus de un técnico.
    """
    authentication_classes = [BellartiAuthenticationMiddleware]

    def patch(self, request: Request, action: str, id: str) -> Response:
        logger.debug("PATCH /after_sales/technician/%s/%s", action, id)
        use_case = TechnicianUseCase(action=action, id=id)
        return use_case.manage_status()
