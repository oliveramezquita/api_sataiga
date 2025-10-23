from rest_framework import views
from rest_framework.request import Request
from rest_framework.response import Response
from api.use_cases.concept_use_case import ConceptUseCase
from api.middlewares import BellartiAuthenticationMiddleware
import logging

logger = logging.getLogger(__name__)


class ConceptsView(views.APIView):
    """
    Endpoint para crear y listar conceptos.

    Métodos:
        POST: Crea un nuevo concepto.
        GET: Lista de conceptos con paginación (page, itemsPerPage).
    """
    authentication_classes = [BellartiAuthenticationMiddleware]

    def post(self, request: Request, project_id: str) -> Response:
        """Crea un nuevo concepto."""
        logger.debug("POST /concepts/%s recibido con datos: %s",
                     project_id, request.data)
        use_case = ConceptUseCase(project_id=project_id, data=request.data)
        response = use_case.save()
        logger.debug("Respuesta POST /concepts: %s",
                     response.data if hasattr(response, 'data') else response)
        return response

    def get(self, request: Request, project_id: str) -> Response:
        """Obtiene la lista paginada de conceptos."""
        logger.debug("GET /concepts/%s con params: %s",
                     project_id, request.query_params)
        use_case = ConceptUseCase(request=request, project_id=project_id)
        response = use_case.get()
        logger.debug("Respuesta GET /concepts: %s",
                     response.data if hasattr(response, 'data') else response)
        return response


class ConceptByIdView(views.APIView):
    """
    Endpoint para operaciones sobre un concepto.

    Métodos:
        GET: Obtiene los detalles del concepto.
        PATCH: Actualiza datos de un concepto existente.
        DELETE: Elimina un concepto.
    """
    authentication_classes = [BellartiAuthenticationMiddleware]

    def get(self, request: Request, id: str) -> Response:
        """Obtiene un concepto por su ID."""
        logger.debug("GET /concept/%s", id)
        use_case = ConceptUseCase(id=id)
        return use_case.get_by_id()

    def patch(self, request: Request, id: str) -> Response:
        """Actualiza un concepto por su ID."""
        logger.debug("PATCH /concept/%s con datos: %s", id, request.data)
        use_case = ConceptUseCase(data=request.data, id=id)
        return use_case.update()

    def delete(self, request: Request, id: str) -> Response:
        """Elimina un concepto por su ID."""
        logger.debug("DELETE /concept/%s", id)
        use_case = ConceptUseCase(id=id)
        return use_case.delete()


class ConceptItemsView(views.APIView):
    """
    Endpoint para procesar los elementos del concepto.

    Métodos:
        PATCH: Actualiza o agrega los elementos.
        DELETE: Elimina un valor en los elementos.
    """
    authentication_classes = [BellartiAuthenticationMiddleware]

    def patch(self, request: Request, id: str, element: str) -> Response:
        """Actualiza los elementos."""
        logger.debug("PATCH /concept/%s/%s con datos: %s",
                     id, element, request.data)
        use_case = ConceptUseCase(data=request.data, id=id, element=element)
        return use_case.process_items()

    def delete(self, request: Request, id: str, element: str) -> Response:
        """Elimina un valor de los elementos del concepto."""
        logger.debug("DELETE /concept/%s/%s con datos: %s",
                     id, element, request.data)
        use_case = ConceptUseCase(data=request.data, id=id, element=element)
        return use_case.delete_item()


class ConceptTemplatesView(views.APIView):
    """
    Endpoint para procesar las plantillas del concepto.

    Métodos:
        PATCH: Actualiza o agrega plantillas al concepto.
    """
    authentication_classes = [BellartiAuthenticationMiddleware]

    def patch(self, request: Request, id: str) -> Response:
        """Actualiza los elementos."""
        logger.debug("PATCH /concept/%s con datos: %s", id, request.data)
        use_case = ConceptUseCase(data=request.data, id=id)
        return use_case.process_templates()


class ConceptIndirectCostsView(views.APIView):
    """
    Endpoint para procesar el porcentaje de indirectos al concepto.

    Métodos:
        PATCH: Añade los costos de indirectos al concepto.
    """
    authentication_classes = [BellartiAuthenticationMiddleware]

    def patch(self, request: Request, id: str) -> Response:
        """Agrega o actualiza los costos indirectos a un Template."""
        logger.debug("PATCH /concept/%s con datos: %s", id, request.data)
        use_case = ConceptUseCase(data=request.data, id=id)
        return use_case.process_indirect_costs()

    def delete(self, request: Request, id: str) -> Response:
        """Limpia los costos indirectos de un Template."""
        logger.debug("DELETE /concept/%s", id)
        use_case = ConceptUseCase(id=id)
        return use_case.clear_indirect_costs()
