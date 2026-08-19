from rest_framework import views
from rest_framework.request import Request
from rest_framework.response import Response
from api.use_cases.customer_use_case import CustomerUseCase
from api.middlewares import BellartiAuthenticationMiddleware
import logging

logger = logging.getLogger(__name__)


class CustomersView(views.APIView):
    """
    Endpoint para crear y listar clientes de Postventa.

    Métodos:
        POST: Crea un nuevo cliente de Postventa.
        GET: Lista clientes con paginación (page, itemsPerPage).
    """
    authentication_classes = [BellartiAuthenticationMiddleware]

    def post(self, request: Request) -> Response:
        """Crea un nuevo proyecto especial."""
        logger.debug(
            "POST /after_sales/customers recibido con datos: %s", request.data)
        use_case = CustomerUseCase(data=request.data)
        response = use_case.save()
        logger.debug("Respuesta POST /after_sales/customers: %s",
                     response.data if hasattr(response, 'data') else response)
        return response

    def get(self, request: Request) -> Response:
        """Obtiene la lista paginada de clientes de Postventa."""
        logger.debug("GET /after_sales/customers con params: %s",
                     request.query_params)
        use_case = CustomerUseCase(request=request)
        response = use_case.get()
        logger.debug("Respuesta GET /after_sales/customers: %s",
                     response.data if hasattr(response, 'data') else response)
        return response


class CustomerByIdView(views.APIView):
    """
    Endpoint para operaciones sobre un cliente de Postventa en específico.

    Métodos:
        GET: Obtiene los detalles del cliente.
        PATCH: Actualiza datos de un cliente existente.
        DELETE: Elimina un cliente.
    """
    authentication_classes = [BellartiAuthenticationMiddleware]

    def get(self, request: Request, id: str) -> Response:
        """Obtiene un cliente de Postventa por su ID."""
        logger.debug("GET /after_sales/customer/%s", id)
        use_case = CustomerUseCase(id=id)
        return use_case.get_by_id()

    def patch(self, request: Request, id: str) -> Response:
        """Actualiza un cliente de Postventa por su ID."""
        logger.debug(
            "PATCH /after_sales/customer/%s con datos: %s", id, request.data)
        use_case = CustomerUseCase(data=request.data, id=id)
        return use_case.update()

    def delete(self, request: Request, id: str) -> Response:
        """Elimina un cliente de Postventa por su ID."""
        logger.debug("DELETE /after_sales/customer/%s", id)
        use_case = CustomerUseCase(id=id)
        return use_case.delete()
