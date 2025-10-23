from rest_framework import views
from rest_framework.request import Request
from rest_framework.response import Response
from api.use_cases.project_use_case import ProjectUseCase
from api.middlewares import BellartiAuthenticationMiddleware
import logging

logger = logging.getLogger(__name__)


class ProjectsView(views.APIView):
    """
    Endpoint para crear y listar proyectos especiales.

    Métodos:
        POST: Crea un nuevo proyecto.
        GET: Lista proyectos con paginación (page, itemsPerPage).
    """
    authentication_classes = [BellartiAuthenticationMiddleware]

    def post(self, request: Request, client_id: str) -> Response:
        """Crea un nuevo proyecto especial."""
        logger.debug(
            "POST /projects/client/%s recibido con datos: %s", client_id, request.data)
        use_case = ProjectUseCase(client_id=client_id, data=request.data)
        response = use_case.save()
        logger.debug("Respuesta POST /projects: %s",
                     response.data if hasattr(response, 'data') else response)
        return response

    def get(self, request: Request, client_id: str) -> Response:
        """Obtiene la lista paginada de proyectos especiales."""
        logger.debug("GET /projects/client/%s con params: %s",
                     client_id, request.query_params)
        use_case = ProjectUseCase(request=request, client_id=client_id)
        response = use_case.get()
        logger.debug("Respuesta GET /projects: %s",
                     response.data if hasattr(response, 'data') else response)
        return response


class ProjectByIdView(views.APIView):
    """
    Endpoint para operaciones sobre un proyecto específico.

    Métodos:
        GET: Obtiene los detalles del proyecto.
        PATCH: Actualiza datos de un proyecto existente.
        DELETE: Elimina un proyecto.
    """
    authentication_classes = [BellartiAuthenticationMiddleware]

    def get(self, request: Request, id: str) -> Response:
        """Obtiene un proyecto especial por su ID."""
        logger.debug("GET /projects/%s", id)
        use_case = ProjectUseCase(id=id)
        return use_case.get_by_id()

    def patch(self, request: Request, id: str) -> Response:
        """Actualiza un proyecto especial por su ID."""
        logger.debug("PATCH /projects/%s con datos: %s", id, request.data)
        use_case = ProjectUseCase(data=request.data, id=id)
        return use_case.update()

    def delete(self, request: Request, id: str) -> Response:
        """Elimina un proyecto especial por su ID."""
        logger.debug("DELETE /projects/%s", id)
        use_case = ProjectUseCase(id=id)
        return use_case.delete()


class ClientsProjectsView(views.APIView):
    """
    Endpoint para obtener clientes tipo PE (Proyecto Especial).
    Permite filtrar con ?q=texto.
    """
    authentication_classes = [BellartiAuthenticationMiddleware]

    def get(self, request: Request) -> Response:
        """Lista clientes tipo PE filtrados por ?q=texto."""
        logger.debug("GET /projects/clients con params: %s",
                     request.query_params)
        use_case = ProjectUseCase(request=request)
        response = use_case.get_clients()
        logger.debug("Respuesta GET /projects/clients: %s",
                     response.data if hasattr(response, 'data') else response)
        return response


class CloneProjectsView(views.APIView):
    authentication_classes = [BellartiAuthenticationMiddleware]

    def post(self, request: Request, client_id: str) -> Response:
        """Clona un proyecto especial."""
        logger.debug(
            "POST /projects/client/%s/clone recibido con datos: %s", client_id, request.data)
        use_case = ProjectUseCase(id=client_id, data=request.data)
        response = use_case.clone_project()
        logger.debug("Respuesta POST /projects: %s",
                     response.data if hasattr(response, 'data') else response)
        return response

    def get(self, request: Request, client_id: str) -> Response:
        logger.debug("GET /projects/clients/%s/clone con params: %s",
                     client_id, request.query_params)
        use_case = ProjectUseCase(client_id=client_id, request=request)
        response = use_case.get_clone_name()
        logger.debug("Respuesta GET /projects/clients: %s",
                     response.data if hasattr(response, 'data') else response)
        return response
