from api.helpers.get_query_params import get_query_params
from api.services.customer_service import CustomerService
from api.services.auth_service import AuthService
from api.decorators.service_method import service_method
from api.helpers.http_responses import ok_paginated, bad_request
from api.utils.pagination_utils import DummyPaginator, DummyPage


class CustomerUseCase:
    def __init__(self, request=None, **kwargs):
        params = get_query_params(request)
        self.q = params["q"]
        self.page = params["page"]
        self.page_size = params["page_size"]
        self.sort_by = params['sort_by']
        self.order_by = params["order_by"]
        self.warranty_type = params.get("warranty_type")
        self.data = kwargs.get("data")
        self.id = kwargs.get("id")
        self.action = kwargs.get("action")
        self.service = CustomerService()
        self.auth_service = AuthService()

    @service_method(success_status="created")
    def save(self):
        """Crea un nuevo cliente para Postventa."""
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
        """Elimina a un cliente."""
        self.service.delete(self.id)
        return "Cliente eliminado correctamente."

    @service_method()
    def manage_status(self):
        """Actualiza el estatus de un cliente dependiendo de la acción."""

        if self.action == 'enable':
            self.auth_service.manage_status(
                'customer', self.id, 1, 'customers')
            return "Cliente habilitado correctamente."
        elif self.action == 'disable':
            self.auth_service.manage_status(
                'customer', self.id, 3, 'customers')
            return "Cliente deshabilitado correctamente."

    def get(self):
        """Método especial con paginación manual."""
        try:
            result = self.service.get_paginated(
                self.warranty_type, self.q, self.page, self.page_size, self.sort_by, self.order_by
            )

            dummy_paginator = DummyPaginator(
                result["count"], result["total_pages"])
            dummy_page = DummyPage(
                result["current_page"], dummy_paginator, result["results"])
            return ok_paginated(dummy_paginator, dummy_page, result["results"])
        except Exception as e:
            return bad_request(f"Error al obtener los clientes: {e}")
