from api.decorators.service_method import service_method
from api.services.contact_service import ContactService


class ContactUseCase:
    """Orquesta peticiones HTTP para el módulo de Contactos."""

    def __init__(self, request=None, **kwargs):
        self.client_id = kwargs.get("client_id", None)
        self.data = kwargs.get("data")
        self.id = kwargs.get("id")
        self.service = ContactService()

    # ----------------------------------------------------------
    # CREAR CONTACTO
    # ----------------------------------------------------------
    @service_method(success_status="created")
    def save(self):
        """
        Crea un nuevo contacto para un cliente.
        """
        self.service.create(self.client_id, self.data)
        return f"Contacto: {self.data['name']} creado exitosamente."

    # ----------------------------------------------------------
    # LISTAR CONTACTOS POR CLIENTE
    # ----------------------------------------------------------
    @service_method()
    def get(self):
        """
        Devuelve todos los contactos de un cliente.
        Si no se pasa client_id, devuelve todos los contactos.
        """
        return self.service.get(self.client_id)

    # ----------------------------------------------------------
    # OBTENER CONTACTO POR ID
    # ----------------------------------------------------------
    @service_method()
    def get_by_id(self):
        """
        Devuelve un contacto por su ID.
        """
        return self.service.get_by_id(self.id)

    # ----------------------------------------------------------
    # ACTUALIZAR CONTACTO
    # ----------------------------------------------------------
    @service_method()
    def update(self):
        """
        Actualiza un contacto existente.
        """
        self.service.update(self.id, self.data)
        return "Contacto actualizado correctamente."

    # ----------------------------------------------------------
    # ELIMINAR CONTACTO
    # ----------------------------------------------------------
    @service_method()
    def delete(self):
        """
        Elimina un contacto existente.
        """
        self.service.delete(self.id)
        return "Contacto eliminado correctamente."
