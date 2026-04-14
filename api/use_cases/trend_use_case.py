from api.decorators.service_method import service_method
from api.helpers.get_query_params import get_query_params
from api.services.trend_service import TrendService
from api.helpers.http_responses import bad_request
from pymongo.errors import DuplicateKeyError


class TrendUseCase:
    """Orquesta peticiones HTTP para el módulo de Tendencias."""

    def __init__(self, request=None, **kwargs):
        params = get_query_params(request)
        self.client_id = params.get("client_id")
        self.front = params.get('front')
        self.data = kwargs.get("data")
        self.id = kwargs.get("id")
        self.service = TrendService()

    @service_method(success_status="created")
    def save(self):
        """Crea una nueva tendencia."""
        try:
            self.service.create(self.data)
            return f"Tendencia: {self.data['front']} creada exitosamente."
        except DuplicateKeyError:
            return bad_request("Ya existe una tendencia para este cliente y este frente.")

    @service_method()
    def add_items(self):
        """Agrega elementos (melaminas/granitos)."""
        self.service.add_items(self.id, self.data)
        return "Los elementos fueron agregados correctamente."

    @service_method()
    def get(self):
        """
        Devuelve todos las tendencias de un cliente.
        Si no se pasa client_id, devuelve todas las tendencias.
        """
        return self.service.get(self.client_id, self.front)

    @service_method()
    def get_by_id(self):
        return self.service.get_by_id(self.id)

    @service_method()
    def delete(self):
        self.service.delete(self.id)
        return "La tendencia ha sido eliminada correctamente."
