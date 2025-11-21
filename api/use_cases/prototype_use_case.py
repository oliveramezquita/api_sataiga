from api.decorators.service_method import service_method
from api.helpers.get_query_params import get_query_params
from api.helpers.http_responses import bad_request, ok_paginated
from api.utils.pagination_utils import DummyPaginator, DummyPage
from api.services.prototype_service import PrototypeService, TendencyValidationError


class PrototypeUseCase:
    def __init__(self, request=None, **kwargs):
        params = get_query_params(request)
        self.q = params["q"]
        self.page = params["page"]
        self.page_size = params["page_size"]
        self.sort_by = params["sort_by"]
        self.order_by = params["order_by"]
        self.client_id = params.get("client_id", None)
        self.front = params.get("front", None)
        self.data = kwargs.get("data", None)
        self.id = kwargs.get("id", None)
        self.service = PrototypeService()

    @service_method(success_status="created")
    def save(self):
        """Crea un nuevo prototipo."""
        self.service.create(self.data)
        return "Prototipo creado correctamente."

    def get(self):
        try:
            result = self.service.get_paginated(
                self.q, self.page, self.page_size, self.sort_by, self.order_by, client=self.client_id, front=self.front
            )

            dummy_paginator = DummyPaginator(
                result["count"], result["total_pages"])
            dummy_page = DummyPage(
                result["current_page"], dummy_paginator, result["results"]
            )

            return ok_paginated(dummy_paginator, dummy_page, result["results"])

        except Exception as e:
            return bad_request(f"Error al obtener prototipos: {e}")

    @service_method()
    def get_by_id(self):
        return self.service.get_by_id(self.id)

    @service_method()
    def update(self):
        try:
            self.service.update(self.id, self.data)
            return "El prototipo ha sido actualizado correctamente."
        except TendencyValidationError as e:
            return bad_request(str(e))

    @service_method()
    def delete(self):
        self.service.delete(self.id)
        return "El prototipo ha sido eliminado correctamente."
