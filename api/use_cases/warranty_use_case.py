from api.decorators.service_method import service_method
from api.services.warranty_service import WarrantyService
from api.helpers.get_query_params import get_query_params


class WarrantyUseCase:
    """Orquesta peticiones HTTP para el módulo de Garantías."""

    def __init__(self, request=None, **kwargs):
        params = get_query_params(request)
        self.q = params["q"]
        self.is_available = params.get('is_available', None)
        self.data = kwargs.get('data')
        self.id = kwargs.get('id')
        self.action = kwargs.get('action')
        self.service = WarrantyService()

    # ----------------------------------------------------------
    # CREAR GARANTIA
    # ----------------------------------------------------------
    @service_method(success_status="created")
    def save(self):
        """
        Crea una nueva garantía.
        """
        self.service.create(self.data)
        return f"Garantía: {self.data['name']} creada exitosamente."

    # ----------------------------------------------------------
    # LISTAR GARANTIAS
    # ----------------------------------------------------------
    @service_method()
    def get(self):
        """
        Devuelve todas las garantías.
        """
        filters = {}

        if self.is_available:
            filters['is_available'] = self.is_available

        return self.service.get(filters)

    # ----------------------------------------------------------
    # OBTENER GARANTIA POR ID
    # ----------------------------------------------------------
    @service_method()
    def get_by_id(self):
        """
        Devuelve una garantía por su ID.
        """
        return self.service.get_by_id(self.id)

    # ----------------------------------------------------------
    # ACTUALIZAR GARANTIA
    # ----------------------------------------------------------
    @service_method()
    def update(self):
        """
        Actualiza una garantía.
        """
        return self.service.update(self.id, self.data)

    @service_method()
    def availability(self):
        """
        Administra la disponibilidad de una garantía.
        """
        if self.action == 'available':
            self.service.availability(self.id, True)
            return "Garantía habilitada correctamente."
        elif self.action == 'unavailable':
            self.service.availability(self.id, False)
            return "Garantía deshabilitada correctamente."
