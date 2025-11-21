from api.decorators.service_method import service_method
from api.helpers.get_query_params import get_query_params
from api_sataiga.handlers.mongodb_handler import MongoDBHandler
from api.helpers.http_responses import bad_request
from api.services.catalog_service import CatalogService, CatalogValidationError


class CatalogUseCase:
    """
    Capa de orquestación (entre vista y servicio).
    No contiene lógica de negocio ni acceso directo a DB.
    """

    def __init__(self, request=None, data=None, id=None):
        params = get_query_params(request)
        self.name = params.get('name', None)
        self.order_by = params.get('orderBy', 'asc')
        self.data = data
        self.id = id
        self.service = CatalogService()

    @service_method(success_status="created")
    def save(self):
        try:
            return self.service.create(self.data)
        except CatalogValidationError as e:
            return bad_request(str(e))

    @service_method()
    def get(self):
        if self.name:
            catalog = self.service.get_by_name(self.name, self.order_by)
            return catalog
        catalogs = self.service.get_all(self.order_by)
        return catalogs

    @service_method()
    def get_by_id(self):
        """Obtiene el catálogo por ID."""
        return self.service.get_by_id(self.id)

    @service_method()
    def update(self):
        try:
            self.service.update(self.id, self.data)
            return "El catálogo ha sido modificado con éxito."
        except CatalogValidationError as e:
            return bad_request(str(e))

    @service_method()
    def delete(self):
        self.service.delete(self.id)
        return "Catálogo eliminado correctamente."
