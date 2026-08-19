from api.decorators.service_method import service_method
from api.services.warranty_service import WarrantyService


class WarrantyUseCase:
    """Orquesta peticiones HTTP para el módulo de Garantias."""

    def __init__(self, request=None, **kwargs):
        self.data = kwargs.get('data')
        self.id = kwargs.get('id')
        self.service = WarrantyService()

    # ----------------------------------------------------------
    # CREAR GARANTIA
    # ----------------------------------------------------------
    @service_method(success_status="created")
    def save(self):
        """
        Crea una nueva garantia.
        """
        self.service.create(self.data)
        return f"Garantía: {self.data['name']} creada exitosamente."

    # ----------------------------------------------------------
    # LISTAR GARANTIAS
    # ----------------------------------------------------------
    @service_method()
    def get(self):
        """
        Devuelve todas las garantias.
        """
        return self.service.get()

    # ----------------------------------------------------------
    # OBTENER GARANTIA POR ID
    # ----------------------------------------------------------
    @service_method()
    def get_by_id(self):
        """
        Devuelve una garantia por su ID.
        """
        return self.service.get_by_id(self.id)

    # ----------------------------------------------------------
    # ACTUALIZAR GARANTIA
    # ----------------------------------------------------------
    @service_method()
    def update(self):
        """
        Actualiza una garantia existente.
        """
        return self.service.update(self.id, self.data)

    @service_method()
    def delete(self):
        """
        Eliminar una garantia existente.
        """
        return self.service.delete(self.id)
