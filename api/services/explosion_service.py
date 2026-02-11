from typing import Any, Dict, Optional
from copy import deepcopy
from api.utils.cache_utils import invalidate_cache
from rest_framework.exceptions import ValidationError
from api.services.base_service import BaseService
from api.helpers.review_required_fields import review_required_fields
from api.repositories.explosion_repository import ExplosionRepository
from api.repositories.trend_repository import TrendRepository
from api.serializers.explosion_serializer import ExplosionSerializer


class ExplosionService(BaseService):
    CACHE_PREFIX = "explosion"

    def __init__(self):
        self.exp_repo = ExplosionRepository()
        self.trend_repo = TrendRepository()

    def get(self, home_production_id: str, supplier_id: Optional[str] = None, status: Optional[int] = None):
        """
        Lista de explosion de materiales aplicando filtros de la od y el proveedor.
        """
        filters = {k: v for k, v in {
            'home_production_id': home_production_id,
            'supplier_id': supplier_id,
        }.items() if v is not None}

        if status is not None:
            filters['status'] = int(status)

        explosion = self._get_all_cached(
            repo=self.exp_repo,
            filters=filters,
            prefix=self.CACHE_PREFIX,
        )
        return ExplosionSerializer(explosion, many=True).data

    def _delete_existing_assignment(self, hp_id: str, prev: Dict[str, Any], trend: Dict[str, Any]) -> None:
        if not hp_id or not isinstance(prev, dict) or not isinstance(trend, dict):
            return

        supplier_prev = prev.get("supplier_id")
        material_prev = prev.get("material_id")
        trend_type = trend.get("type")
        trend_id = trend.get("id")

        if not supplier_prev or not material_prev or not trend_type or not trend_id:
            return

        trend_exp = self.exp_repo.find_one({
            "supplier_id": supplier_prev,
            "home_production_id": hp_id,
            "material_id": material_prev,
        })

        # ✅ Tipo seguro para el type checker y para runtime
        if not isinstance(trend_exp, dict):
            return

        assigned_to_root = trend_exp.get("assigned_to")
        if not isinstance(assigned_to_root, dict):
            return

        assigned_to = assigned_to_root.get(trend_type)
        if not isinstance(assigned_to, dict):
            return

        entry = assigned_to.get(trend_id)
        if not isinstance(entry, dict):
            return

        supplier_id = entry.get("supplier_id")
        material_id = entry.get("material_id")
        if not supplier_id or not material_id:
            return

        exp = self.exp_repo.find_one({
            "supplier_id": supplier_id,
            "home_production_id": hp_id,
            "material_id": material_id,
        })

        if not isinstance(exp, dict):
            return

        self._delete(
            self.exp_repo,
            _id=str(exp.get("_id")),
            cache_prefix=self.CACHE_PREFIX
        )

    def assign(self, data: Dict[str, Any]):
        required_fields = {
            "supplier_id": str,
            "home_production_id": str,
            "material_id": str,
            "explosion": list,
            "gran_total": (int, float),
            "assigned_to": dict,
            "trend": dict,
            "prev": dict,
        }

        review_required_fields(required_fields, data)

        prev = data["prev"]
        trend = data["trend"]

        # 2) Validaciones específicas de prev/trend
        for k in ("supplier_id", "material_id"):
            if not prev.get(k) or not isinstance(prev.get(k), str):
                raise ValidationError(f"El valor prev.{k} es requerido.")

        for k in ("type", "id"):
            if not trend.get(k) or not isinstance(trend.get(k), str):
                raise ValidationError(f"El valor trend.{k} es requerido.")

        trend_type = trend["type"]
        trend_id = trend["id"]

        # 3) Copiar assigned_to (no mutar input)
        assigned_to = deepcopy(data["assigned_to"])

        # asegurar estructura: assigned_to[trend_type] debe ser dict
        if trend_type not in assigned_to or not isinstance(assigned_to.get(trend_type), dict):
            assigned_to[trend_type] = {}

        prev_query = {
            "home_production_id": data["home_production_id"],
            "supplier_id": prev["supplier_id"],
            "material_id": prev["material_id"],
        }

        # revisar nuevamente si existe alguna asignación previa
        current_assign_to = assigned_to.get(trend_type)
        if isinstance(current_assign_to, dict) and not current_assign_to:
            exp = self.exp_repo.find_one(prev_query)

            if isinstance(exp, dict):
                prev_assigned = exp.get('assigned_to', {})

                if isinstance(prev_assigned, dict) and trend_type in prev_assigned:
                    assigned_to[trend_type] = prev_assigned[trend_type]

        self._delete_existing_assignment(
            data["home_production_id"], prev, trend)

        assigned_to[trend_type][trend_id] = {
            "supplier_id": data["supplier_id"],
            "material_id": data["material_id"],
        }

        # 4) Upsert previo: actualizar assigned_to
        self.exp_repo.upsert_one(prev_query, {"assigned_to": assigned_to})

        # 5) Upsert nuevo: crear/actualizar material asignado (sin assigned_to/trend/prev)
        new_query = {
            "home_production_id": data["home_production_id"],
            "supplier_id": data["supplier_id"],
            "material_id": data["material_id"],
        }
        new_set_data = {k: v for k, v in data.items() if k not in {
            "assigned_to", "trend", "prev"}}
        self.exp_repo.upsert_one(new_query, {**new_set_data, 'status': 0})
        invalidate_cache(self.CACHE_PREFIX)
        return True
