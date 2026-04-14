import logging
from typing import Any, Dict

from celery import shared_task
from celery.utils.log import get_task_logger

from api.utils.cache_utils import invalidate_cache
from api.helpers.unique_colors import unique_colors
from api.repositories.explosion_repository import ExplosionRepository
from api.repositories.trend_repository import TrendRepository

# Usa logger de Celery para asegurarte que caiga en el logfile del worker
logger = get_task_logger(__name__)


@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=True, max_retries=5)
def assignments(self, trend_data: Dict[str, Any], exp_data: Dict[str, Any]):
    exp_repo = ExplosionRepository()
    trend_repo = TrendRepository()

    # Extracción defensiva
    client_id = (trend_data or {}).get("client_id")
    front = (trend_data or {}).get("front")

    hp_id = (exp_data or {}).get("home_production_id")
    exp_trend = (exp_data or {}).get("trend") or {}
    exp_trend_type = exp_trend.get("type")

    prev = (exp_data or {}).get("prev") or {}
    supplier_id = prev.get("supplier_id")
    material_id = prev.get("material_id")

    # Queries
    trend = trend_repo.find_one({"client_id": client_id, "front": front})
    exp = exp_repo.find_one({
        "supplier_id": supplier_id,
        "home_production_id": hp_id,
        "material_id": material_id,
    })

    if not trend and not exp:
        logger.info("EXIT: trend and exp not found")
        return

    if not trend:
        logger.info("EXIT: trend not found client_id=%s front=%s",
                    client_id, front)
        return

    if not exp:
        logger.info("EXIT: exp not found supplier_id=%s hp_id=%s material_id=%s",
                    supplier_id, hp_id, material_id)
        return

    assigned_to = exp.get("assigned_to")
    if not isinstance(assigned_to, dict):
        logger.info("EXIT: assigned_to missing or not dict (got=%s)",
                    type(assigned_to).__name__)
        return

    assigned_to_type = assigned_to.get(exp_trend_type)
    # Aquí decides: si dict vacío debe ser válido, NO chequees `not assigned_to_type`, solo el tipo.
    if not isinstance(assigned_to_type, dict):
        logger.info(
            "EXIT: assigned_to[%s] not dict (got=%s)",
            exp_trend_type, type(assigned_to_type).__name__
        )
        return

    trend_type = trend.get(exp_trend_type)
    if not isinstance(trend_type, list):
        logger.info(
            "EXIT: trend[%s] not list (got=%s)",
            exp_trend_type, type(trend_type).__name__
        )
        return

    colors = unique_colors(trend_type)
    if len(colors) == len(assigned_to_type):
        exp_repo.update(str(exp.get('_id')), {'status': 1})
        invalidate_cache('explosion')
