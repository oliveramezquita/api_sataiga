from django.core.paginator import Paginator
from api.helpers.http_responses import created, ok, ok_paginated, not_found, bad_request
from api.serializers.project_serializer import ProjectSerializer
from api.serializers.project_data_serializer import ProjectDataSerializer
from api.services.project_service import ProjectService
from api.helpers.get_query_params import get_query_params


class ProjectUseCase:
    """Orquesta peticiones HTTP para el módulo de Proyectos."""

    def __init__(self, request=None, **kwargs):
        params = get_query_params(request)
        self.page = params["page"]
        self.page_size = params["page_size"]
        self.q = params["q"]
        self.name = params.get("name", None)
        self.data = kwargs.get('data')
        self.id = kwargs.get('id')
        self.client_id = kwargs.get('client_id', None)
        self.service = ProjectService()

    def save(self):
        try:
            new_id = self.service.create(self.data)
            return created({'id': new_id})
        except ValueError as e:
            return bad_request(str(e))
        except LookupError as e:
            return bad_request(str(e))
        except Exception as e:
            return bad_request(f'Error inesperado: {e}')

    def get(self):
        projects = self.service.get_all()
        paginator = Paginator(projects, per_page=self.page_size)
        page = paginator.get_page(self.page)
        serialized = ProjectSerializer(page.object_list, many=True).data
        return ok_paginated(paginator, page, serialized)

    def get_by_id(self):
        try:
            project = self.service.get_by_id(self.id)
            return ok(ProjectSerializer(project).data)
        except LookupError as e:
            return not_found(str(e))

    def update(self):
        try:
            self.service.update(self.id, self.data)
            return ok('El proyecto especial ha sido actualizado correctamente.')
        except LookupError as e:
            return not_found(str(e))
        except Exception as e:
            return bad_request(f'Error inesperado: {e}')

    def delete(self):
        try:
            self.service.delete(self.id)
            return ok('Proyecto especial eliminado correctamente.')
        except LookupError as e:
            return not_found(str(e))
        except Exception as e:
            return bad_request(f'Error inesperado: {e}')

    def get_clients(self):
        """Obtiene lista de clientes tipo PE con búsqueda opcional."""
        try:
            clients = self.service.get_clients(self.q)
            serialized = ProjectDataSerializer(clients, many=True).data
            return ok(serialized)
        except Exception as e:
            return bad_request(f'Error al obtener los clientes: {e}')

    def get_clone_name(self):
        try:
            if self.name:
                clone_name = self.service.get_clone_name(
                    self.client_id, self.name)
                return ok(clone_name)
            return ok("")
        except LookupError as e:
            return not_found(str(e))
        except Exception as e:
            return bad_request(f'Error inesperado: {e}')

    def clone_project(self):
        try:
            self.service.clone_project(self.id, self.data.get('name', None))
            return ok('El proyecto ha sido clonado correctamente.')
        except LookupError as e:
            return not_found(str(e))
        except Exception as e:
            return bad_request(f'Error inesperado: {e}')
