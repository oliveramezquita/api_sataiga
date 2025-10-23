from django.core.paginator import Paginator
from api.helpers.http_responses import created, ok, ok_paginated, not_found, bad_request
from api.serializers.concept_serializer import ConceptSerializer
from api.services.concept_service import ConceptService
from api.helpers.get_query_params import get_query_params


class ConceptUseCase:
    """Orquesta peticiones HTTP para el módulo de Conceptos."""

    def __init__(self, request=None, **kwargs):
        params = get_query_params(request)
        self.page = params["page"]
        self.page_size = params["page_size"]
        self.q = params["q"]
        self.data = kwargs.get('data')
        self.id = kwargs.get('id')
        self.project_id = kwargs.get('project_id', None)
        self.element = kwargs.get('element', None)
        self.service = ConceptService()

    def save(self):
        try:
            name = self.service.create({
                **self.data,
                'project_id': self.project_id})
            return created(f'Concepto: {name} creado exitosamente.')
        except ValueError as e:
            return bad_request(str(e))
        except LookupError as e:
            return bad_request(str(e))
        except Exception as e:
            return bad_request(f'Error inesperado: {e}')

    def get(self):
        concepts = self.service.get_all(project_id=self.project_id)
        paginator = Paginator(concepts, per_page=self.page_size)
        page = paginator.get_page(self.page)
        serialized = ConceptSerializer(page.object_list, many=True).data
        return ok_paginated(paginator, page, serialized)

    def get_by_id(self):
        try:
            concept = self.service.get_by_id(self.id)
            return ok(ConceptSerializer(concept).data)
        except LookupError as e:
            return not_found(str(e))

    def update(self):
        try:
            self.service.update(self.id, self.data)
            return ok('El concepto ha sido actualizado correctamente.')
        except LookupError as e:
            return not_found(str(e))
        except Exception as e:
            return bad_request(f'Error inesperado: {e}')

    def delete(self):
        try:
            self.service.delete(self.id)
            return ok('Concepto eliminado correctamente.')
        except LookupError as e:
            return not_found(str(e))
        except Exception as e:
            return bad_request(f'Error inesperado: {e}')

    def process_items(self):
        try:
            self.service.process_items(self.id, self.element, self.data)
            return ok('Los elementos fueron agregados y/o modificados correctamente.')
        except LookupError as e:
            return not_found(str(e))
        except Exception as e:
            return bad_request(f'Error inesperado: {e}')

    def delete_item(self):
        try:
            self.service.delete_item(self.id, self.element, self.data['id'])
            return ok('El elemento fue eliminado correctamente.')
        except LookupError as e:
            return not_found(str(e))
        except Exception as e:
            return bad_request(f'Error inesperado: {e}')

    def process_templates(self):
        try:
            self.service.process_templates(self.id, self.data)
            return ok('Las plantillas fueron agregadas y/o modificadas correctamente.')
        except LookupError as e:
            return not_found(str(e))
        except Exception as e:
            return bad_request(f'Error inesperado: {e}')

    def process_indirect_costs(self):
        try:
            indirect_costs = self.data.get("indirect_costs")
            self.service.process_indirect_costs(self.id, indirect_costs)
            return ok("Indirectos actualizados correctamente.")
        except LookupError as e:
            return not_found(str(e))
        except Exception as e:
            return bad_request(f'Error inesperado: {e}')

    def clear_indirect_costs(self):
        try:
            self.service.clear_indirect_costs(self.id)
            return ok("El costo indirecto se eliminó correctamente.")
        except LookupError as e:
            return not_found(str(e))
        except Exception as e:
            return bad_request(f'Error inesperado: {e}')
