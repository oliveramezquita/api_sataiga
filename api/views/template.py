from rest_framework import views
from rest_framework.request import Request
from rest_framework.response import Response
from api.use_cases.template_use_case import TemplateUseCase
from api.middlewares import BellartiAuthenticationMiddleware
import logging

logger = logging.getLogger(__name__)


class TemplatesView(views.APIView):
    """
    Endpoint para crear y listar plantillas.

    Métodos:
        POST: Crea una nueva plantilla.
        GET: Lista de plantillas con paginación (page, itemsPerPage).
    """
    authentication_classes = [BellartiAuthenticationMiddleware]

    def post(self, request: Request) -> Response:
        """Crea una nueva plantilla."""
        logger.debug("POST /templates recibido con datos: %s", request.data)
        use_case = TemplateUseCase(data=request.data)
        response = use_case.save()
        logger.debug("Respuesta POST /templates: %s",
                     response.data if hasattr(response, 'data') else response)
        return response

    def get(self, request: Request) -> Response:
        """Obtiene la lista paginada de plantillas."""
        logger.debug("GET /templates con params: %s", request.query_params)
        use_case = TemplateUseCase(request=request)
        response = use_case.get()
        logger.debug("Respuesta GET /templates: %s",
                     response.data if hasattr(response, 'data') else response)
        return response


class TemplateByIdView(views.APIView):
    """
    Endpoint para operaciones sobre una plantilla.

    Métodos:
        GET: Obtiene los detalles de la plantilla.
        PATCH: Actualiza datos de una plantilla existente.
        DELETE: Elimina una plantilla.
    """
    authentication_classes = [BellartiAuthenticationMiddleware]

    def get(self, request: Request, id: str) -> Response:
        """Obtiene una plantilla por su ID."""
        logger.debug("GET /template/%s", id)
        use_case = TemplateUseCase(id=id)
        return use_case.get_by_id()

    def patch(self, request: Request, id: str) -> Response:
        """Actualiza una plantilla por su ID."""
        logger.debug("PATCH /template/%s con datos: %s", id, request.data)
        use_case = TemplateUseCase(data=request.data, id=id)
        return use_case.update()

    def delete(self, request: Request, id: str) -> Response:
        """Elimina una plantilla por su ID."""
        logger.debug("DELETE /template/%s", id)
        use_case = TemplateUseCase(id=id)
        return use_case.delete()


class TemplateItemsView(views.APIView):
    """
    Endpoint para procesar los elementos de la plantilla.

    Métodos:
        PATCH: Actualiza o agrega los elementos.
        DELETE: Elimina un valor en los elementos.
    """
    authentication_classes = [BellartiAuthenticationMiddleware]

    def patch(self, request: Request, id: str, element: str) -> Response:
        """Actualiza los elementos."""
        logger.debug("PATCH /template/%s/%s con datos: %s",
                     id, element, request.data)
        use_case = TemplateUseCase(data=request.data, id=id, element=element)
        return use_case.process_items()

    def delete(self, request: Request, id: str, element: str) -> Response:
        """Elimina un valor de los elementos de la plantilla."""
        logger.debug("DELETE /template/%s/%s con datos: %s",
                     id, element, request.data)
        use_case = TemplateUseCase(data=request.data, id=id, element=element)
        return use_case.delete_item()


class TemplateIndirectCostsView(views.APIView):
    """
    Endpoint para procesar el porcentaje de indirectos al template.

    Métodos:
        PATCH: Añade los costos de indirectos al template.
    """
    authentication_classes = [BellartiAuthenticationMiddleware]

    def patch(self, request: Request, id: str) -> Response:
        """Agrega o actualiza los costos indirectos a un Template."""
        logger.debug("PATCH /template/%s con datos: %s", id, request.data)
        use_case = TemplateUseCase(data=request.data, id=id)
        return use_case.process_indirect_costs()

    def delete(self, request: Request, id: str) -> Response:
        """Limpia los costos indirectos de un Template."""
        logger.debug("DELETE /template/%s", id)
        use_case = TemplateUseCase(id=id)
        return use_case.clear_indirect_costs()
