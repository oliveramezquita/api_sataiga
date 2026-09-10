from typing import Optional, Dict, Any
from api.services.base_service import BaseService
from api.repositories.warranty_repository import WarrantyRepository
from api.serializers.warranty_serializer import WarrantySerializer
from api.helpers.clean_payload import clean_payload
from api.helpers.formats import to_float
from api.utils.cache_utils import invalidate_cache


class WarrantyService(BaseService):
    """Lógica de negocio pura para las Garantías."""

    CACHE_PREFIX = "warranties"

    def __init__(self):
        self.warranty_repo = WarrantyRepository()

    # ----------------------------------------------------------
    # CREAR GARANTIA
    # ----------------------------------------------------------
    def create(self, data: Dict[str, Any]) -> Dict[str, str]:
        """
        Crea una garantía.
        """
        if 'duration' in data:
            data['duration'] = to_float(data['duration'])

        self._create(
            repo=self.warranty_repo,
            data=clean_payload({**data, 'is_available': True}),
            required_fields=["name", "duration"],
            cache_prefix=self.CACHE_PREFIX,
        )

    # ----------------------------------------------------------
    # LISTADO (con cache por filtro)
    # ----------------------------------------------------------
    def get(self, filters: dict):
        """
        Lista las garantías.
        """
        warranties = self._get_all_cached(
            repo=self.warranty_repo,
            filters=filters,
            prefix=self.CACHE_PREFIX,
        )
        return WarrantySerializer(warranties, many=True).data

    # ----------------------------------------------------------
    # OBTENER POR ID
    # ----------------------------------------------------------
    def get_by_id(self, warranty_id: str):
        """
        Devuelve una garantía por su ID.
        """
        return self._get_by_id(self.warranty_repo, warranty_id, serializer=WarrantySerializer)

    # ----------------------------------------------------------
    # ACTUALIZAR
    # ----------------------------------------------------------
    def update(self, warranty_id: str, data: Dict[str, Any]) -> str:
        """
        Actualiza una garantía existente.
        """
        if 'duration' in data:
            data['duration'] = to_float(data['duration'])

        self._update(
            repo=self.warranty_repo,
            _id=warranty_id,
            data=data,
            cache_prefix=self.CACHE_PREFIX,
        )
        return "Garantía actualizada correctamente."

    # ----------------------------------------------------------
    # HABILITAR
    # ----------------------------------------------------------
    def availability(self, warranty_id: str, is_available: bool):
        """
        Administra la disponibilidad de una garantía.
        """
        self._update(
            repo=self.warranty_repo,
            _id=warranty_id,
            data={'is_available': is_available},
            cache_prefix=self.CACHE_PREFIX,
        )
