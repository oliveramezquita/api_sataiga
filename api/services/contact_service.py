from typing import Optional, Dict, Any
from api.services.base_service import BaseService
from api.repositories.contact_repository import ContactRepository
from api.repositories.client_repository import ClientRepository
from api.serializers.contact_serializer import ContactSerializer


class ContactService(BaseService):
    """Lógica de negocio pura para Contactos."""

    CACHE_PREFIX = "contacts"

    def __init__(self):
        self.contact_repo = ContactRepository()
        self.client_repo = ClientRepository()

    # ----------------------------------------------------------
    # CREAR CONTACTO
    # ----------------------------------------------------------
    def create(self, client_id: str, data: Dict[str, Any]) -> Dict[str, str]:
        """
        Crea un contacto asociado a un cliente existente.
        Valida que el cliente exista por su ID.
        """
        # 1) Validar existencia del cliente
        client = self.client_repo.find_by_id(client_id)
        if not client:
            raise LookupError("El cliente no existe.")

        # 2) Validar campos requeridos del contacto
        #    (además de client_id, exigimos al menos 'name')
        self._validate_fields(data, ["name"])

        # 3) Insertar contacto: aseguramos que el client_id del argumento prevalezca
        payload = {**data, "client_id": client_id}
        inserted_id = self._create(
            repo=self.contact_repo,
            data=payload,
            required_fields=["client_id", "name"],
            cache_prefix=self.CACHE_PREFIX,
        )
        return {"id": str(inserted_id)}

    # ----------------------------------------------------------
    # LISTADO (con cache por filtro)
    # ----------------------------------------------------------
    def get(self, client_id: Optional[str] = None):
        """
        Lista contactos; si se pasa client_id, filtra por cliente.
        """
        filters = {"client_id": client_id} if client_id else None
        contacts = self._get_all_cached(
            repo=self.contact_repo,
            filters=filters,
            prefix=self.CACHE_PREFIX,
        )
        return ContactSerializer(contacts, many=True).data

    # ----------------------------------------------------------
    # OBTENER POR ID
    # ----------------------------------------------------------
    def get_by_id(self, contact_id: str):
        """
        Devuelve un contacto por su ID.
        """
        return self._get_by_id(self.contact_repo, contact_id, serializer=ContactSerializer)

    # ----------------------------------------------------------
    # ACTUALIZAR
    # ----------------------------------------------------------
    def update(self, contact_id: str, data: Dict[str, Any]) -> str:
        """
        Actualiza un contacto existente.
        """
        self._update(
            repo=self.contact_repo,
            _id=contact_id,
            data=data,
            cache_prefix=self.CACHE_PREFIX,
        )
        return "Contacto actualizado correctamente."

    # ----------------------------------------------------------
    # ELIMINAR
    # ----------------------------------------------------------
    def delete(self, contact_id: str) -> str:
        """
        Elimina un contacto existente.
        """
        self._delete(
            repo=self.contact_repo,
            _id=contact_id,
            cache_prefix=self.CACHE_PREFIX,
        )
        return "Contacto eliminado correctamente."
