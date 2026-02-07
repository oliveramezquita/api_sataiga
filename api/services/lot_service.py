from collections import Counter
from typing import Any, Dict, List, Tuple
from rest_framework.exceptions import ValidationError
from api.services.base_service import BaseService
from api.repositories.lot_repository import LotRepository
from api.repositories.home_production_repository import HomeProductionRepository
from api.serializers.lot_serializer import LotSerializer
from api.functions.explosion import explosion


class LotService(BaseService):
    CACHE_PREFIX = "lots"

    def __init__(self):
        self.lot_repo = LotRepository()
        self.hp_repo = HomeProductionRepository()

    @staticmethod
    def _default_progress() -> Dict[str, Any]:
        def block():
            return {"stages": [], "percentage": 0.0}

        return {
            "cocina": block(),
            "closet": block(),
            "puertas": block(),
            "mdeb": block(),
            "waldras": block(),
            "instalacion": block(),
        }

    @staticmethod
    def split_and_process_lots(data: Any) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        insertions: List[Dict[str, Any]] = []
        updates: List[Dict[str, Any]] = []

        if data is None:
            return insertions, updates
        if not isinstance(data, list):
            raise ValidationError("lots debe ser una lista.")

        for item in data:
            if not isinstance(item, dict):
                continue  # o ValidationError

            _id = item.get("_id")
            if _id:
                updates.append(item)
            else:
                insertions.append(item)

        return insertions, updates

    def _update_hp_lots(self, home_production_id: str, lots: List[Dict[str, Any]]):
        if home_production_id and lots:
            prototype_counter = Counter()
            for lot in lots:
                prototype_counter[lot['prototype']] += 1

            result = {
                'total': len(lots),
                'prototypes': dict(prototype_counter),
            }

            total_sum = sum(float(l["percentage"]) for l in lots)
            self._update(
                repo=self.hp_repo,
                _id=home_production_id,
                data={
                    'lots': result,
                    'progress': round(total_sum / len(lots), 2)},
                cache_prefix='home_production'
            )

    def create(self, home_production_id: str, data: Dict[str, Any]):
        if not home_production_id:
            raise ValidationError("home_production_id es requerido.")

        lots = data.get("lots")
        if not lots:
            # respuesta consistente
            return {"success": [], "errors": []}

        insertions, updates = self.split_and_process_lots(lots)

        errors: List[Dict[str, Any]] = []

        # -------- Updates --------
        for lot in updates:
            _id = lot.get("_id")
            if not _id:
                errors.append(
                    {"lot": lot, "error": "Falta _id para actualizar."})
                continue

            # no mutar input
            payload = {k: v for k, v in lot.items() if k != "_id"}

            # fuerza relación (evita que alguien cambie HP)
            payload["home_production_id"] = home_production_id

            try:
                self._update(
                    repo=self.lot_repo,
                    _id=_id,
                    data=payload,
                    cache_prefix=self.CACHE_PREFIX,
                )
            except Exception as e:
                errors.append(lot)

        for lot in insertions:
            payload = {
                "home_production_id": home_production_id,
                **lot,
                "percentage": 0,
                "progress": self._default_progress(),
            }

            try:
                self._create(
                    repo=self.lot_repo,
                    data=payload,
                    required_fields=["prototype", "block", "lot", "laid"],
                    cache_prefix=self.CACHE_PREFIX,
                )
            except Exception as e:
                errors.append(lot)

        updated_lots = self.lot_repo.find_all(
            {"home_production_id": home_production_id})
        self._update_hp_lots(home_production_id, updated_lots)
        explosion.delay(home_production_id)
        return {
            "success": LotSerializer(updated_lots, many=True).data,
            "errors": errors,
        }
