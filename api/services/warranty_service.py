from typing import Optional, Dict, Any
from api.services.base_service import BaseService
from api.repositories.warranty_repository import WarrantyRepository
from api.serializers.warranty_serializer import WarrantySerializer
from api.helpers.clean_payload import clean_payload
from api.helpers.formats import to_float


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
        Crea una garantia.
        """
        if 'duration' in data:
            data['duration'] = to_float(data['duration'])

        self._create(
            repo=self.warranty_repo,
            data=clean_payload({**data, 'warranty_status': 1, 'status': 1}),
            required_fields=["name", "duration"],
            cache_prefix=self.CACHE_PREFIX,
        )

    # ----------------------------------------------------------
    # LISTADO (con cache por filtro)
    # ----------------------------------------------------------
    def get(self):
        """
        Lista las garantias.
        """
        warranties = self._get_all_cached(
            repo=self.warranty_repo,
            filters={'status': 1},
            prefix=self.CACHE_PREFIX,
        )
        return WarrantySerializer(warranties, many=True).data

    # ----------------------------------------------------------
    # OBTENER POR ID
    # ----------------------------------------------------------
    def get_by_id(self, warranty_id: str):
        """
        Devuelve una garantia por su ID.
        """
        return self._get_by_id(self.warranty_repo, warranty_id, serializer=WarrantySerializer)

    # ----------------------------------------------------------
    # ACTUALIZAR
    # ----------------------------------------------------------
    def update(self, warranty_id: str, data: Dict[str, Any]) -> str:
        """
        Actualiza una garantia existente.
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
    # ELIMINAR
    # ----------------------------------------------------------
    def delete(self, warranty_id: str):
        """
        Eliminar una garantia existente.
        """
        self._update(
            repo=self.warranty_repo,
            _id=warranty_id,
            data={'status': 0},
            cache_prefix=self.CACHE_PREFIX,
        )
        return "Garantía eliminada correctamente."
