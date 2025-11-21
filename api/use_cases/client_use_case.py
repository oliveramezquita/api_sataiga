from api.decorators.service_method import service_method
from api.services.client_service import ClientService
from api.helpers.http_responses import ok_paginated, bad_request
from api.utils.pagination_utils import DummyPaginator, DummyPage
from api.helpers.get_query_params import get_query_params


class ClientUseCase:
    def __init__(self, request=None, **kwargs):
        params = get_query_params(request)
        self.q = params["q"]
        self.page = params["page"]
        self.page_size = params["page_size"]
        self.sort_by = params['sort_by']
        self.order_by = params["order_by"]
        self.data = kwargs.get("data")
        self.id = kwargs.get("id")
        self.client_type = kwargs.get("client_type")
        self.service = ClientService()

    @service_method(success_status="created")
    def save(self):
        """Crea un nuevo cliente."""
        self.service.create(self.data)
        return f"Cliente: {self.data['name']} creado exitosamente."

    @service_method()
    def get_by_id(self):
        """Obtiene cliente por ID."""
        return self.service.get_by_id(self.id)

    @service_method()
    def update(self):
        """Actualiza un cliente existente."""
        self.service.update(self.id, self.data)
        return "El cliente ha sido actualizado correctamente."

    @service_method()
    def delete(self):
        """Elimina un cliente."""
        self.service.delete(self.id)
        return "Cliente eliminado correctamente."

    def get(self):
        """Método especial con paginación manual."""
        try:
            result = self.service.get_paginated(
                self.client_type, self.q, self.page, self.page_size, self.sort_by, self.order_by
            )

            dummy_paginator = DummyPaginator(
                result["count"], result["total_pages"])
            dummy_page = DummyPage(
                result["current_page"], dummy_paginator, result["results"])
            return ok_paginated(dummy_paginator, dummy_page, result["results"])
        except Exception as e:
            return bad_request(f"Error al obtener los clientes: {e}")
