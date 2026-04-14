from typing import Any, Dict, List
from decimal import Decimal, ROUND_HALF_UP
from copy import deepcopy
from celery import shared_task
from celery.utils.log import get_task_logger
from api.utils.cache_utils import invalidate_cache
from api.helpers.formats import to_float
from api.repositories.home_production_repository import HomeProductionRepository
from api.repositories.volumetry_repository import VolumetryRepository
from api.repositories.explosion_repository import ExplosionRepository

logger = get_task_logger(__name__)


def r2(x: Any) -> float:
    return round(float(x or 0), 2)


def total_from_prototypes(prototypes: List[Dict[str, Any]]) -> float:
    """Suma factory + installation + delivery de todos los prototypes (YA multiplicados)."""
    total = 0.0
    for p in prototypes or []:
        q = p.get("quantities") or {}
        total += to_float(q.get("factory", 0)) + \
            to_float(q.get("installation", 0)) + to_float(q.get("delivery", 0))
    return r2(total)


def upsert_prototype(area: Dict[str, Any], prototype: str, quantities: Dict[str, Any]) -> Dict[str, Any]:
    prototypes = area.setdefault("prototypes", [])

    for item in prototypes:
        if item.get("prototype") == prototype:
            item["quantities"] = quantities
            area["total"] = total_from_prototypes(prototypes)
            return area

    prototypes.append({
        "prototype": prototype,
        "quantities": quantities,
    })
    area["total"] = total_from_prototypes(prototypes)
    return area


def create_amounts(item: Dict[str, Any], hp: Dict[str, Any]) -> List[Dict[str, Any]]:
    lots_prototypes = (hp.get("lots") or {}).get("prototypes") or {}
    prototype = item.get("prototype")

    # Si el prototype no está contemplado en lots, no hay nada que mover
    if not prototype or prototype not in lots_prototypes:
        return []

    multiplier = to_float(lots_prototypes.get(
        prototype, 0), 0.0, min_value=0.0)

    areas_out: List[Dict[str, Any]] = []
    for v in (item.get("volumetry") or []):
        area = v.get("area")
        if not area:
            continue

        factory = r2(to_float(v.get("factory", 0),
                     0.0, min_value=0.0) * multiplier)
        installation = r2(to_float(v.get("installation", 0),
                          0.0, min_value=0.0) * multiplier)
        delivery = r2(to_float(v.get("delivery", 0),
                      0.0, min_value=0.0) * multiplier)
        total = r2(factory + installation + delivery)

        if total > 0:
            prototypes = [{
                "prototype": prototype,
                "quantities": {
                    "factory": factory,
                    "installation": installation,
                    "delivery": delivery,
                },
            }]
            areas_out.append({
                "area": area,
                "prototypes": prototypes,
                "total": total_from_prototypes(prototypes),  # consistente
            })

    return areas_out


def get_area_data(data: List[Dict[str, Any]], area_name: str) -> Dict[str, Any]:
    for item in data:
        if item.get("area") == area_name:
            return {
                "area": area_name,
                "prototypes": item.get("prototypes", []),
                "total": item.get("total", 0)
            }
    return {
        "area": area_name,
        "prototypes": [],
        "total": 0
    }


def update_amounts(current_exp: Dict[str, Any], item: Dict[str, Any], hp: Dict[str, Any]) -> List[Dict[str, Any]]:
    exp = current_exp.get('explosion', [])
    areas = {e["area"]: e for e in exp}
    lots_prototypes = (hp.get("lots") or {}).get("prototypes") or {}
    prototype = item.get("prototype")

    if not prototype or prototype not in lots_prototypes:
        return exp

    multiplier = to_float(lots_prototypes.get(
        prototype, 0), 0.0, min_value=0.0)

    for v in (item.get("volumetry") or []):
        factory = r2(to_float(v.get("factory", 0),
                     0.0, min_value=0.0) * multiplier)
        installation = r2(to_float(v.get("installation", 0),
                          0.0, min_value=0.0) * multiplier)
        delivery = r2(to_float(v.get("delivery", 0),
                      0.0, min_value=0.0) * multiplier)
        total = r2(factory + installation + delivery)
        if total > 0:
            area = v.get("area")
            if not area:
                continue

            result = get_area_data(exp, area)
            result = upsert_prototype(result, prototype, {
                "factory": factory,
                "installation": installation,
                "delivery": delivery,
            })
            areas[result["area"]] = result
    return list(areas.values())


def merge_explosion(current_explosion: list, volumetry: list) -> list:
    merged = list(current_explosion)

    existing_keys = {
        (item.get("material_id"), item.get("supplier_id"))
        for item in current_explosion
    }

    for item in volumetry:
        material_id = item.get("material_id")
        supplier_id = item.get("supplier_id")

        if not material_id or not supplier_id:
            continue  # ignora registros mal formados

        key = (material_id, supplier_id)

        if key not in existing_keys:
            merged.append(item)
            existing_keys.add(key)

    return merged


def scale_explosion(data: Dict[str, Any], prev: float, current: float) -> Dict[str, Any]:
    if prev == 0:
        raise ValueError("prev no puede ser 0")
    if current < 0 or prev < 0:
        raise ValueError("prev y current deben ser >= 0")

    result = deepcopy(data)

    factor = Decimal(str(current)) / Decimal(str(prev))

    def scale(value):
        return float(
            (Decimal(str(value)) * factor).quantize(Decimal("0.01"),
                                                    rounding=ROUND_HALF_UP)
        )

    new_gran_total = Decimal("0")

    for area in result.get("explosion", []):
        new_area_total = Decimal("0")

        for proto in area.get("prototypes", []):
            quantities = proto.get("quantities", {})
            for key in ("factory", "installation", "delivery"):
                if key in quantities and quantities[key] is not None:
                    new_value = scale(quantities[key])
                    quantities[key] = new_value
                    new_area_total += Decimal(str(new_value))

        area["total"] = float(new_area_total.quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP))
        new_gran_total += new_area_total

    result["gran_total"] = float(new_gran_total.quantize(
        Decimal("0.01"), rounding=ROUND_HALF_UP))
    return result


@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=True, max_retries=5)
def explosion(self, home_production_id: str, prev_lots: int):
    hp_repo = HomeProductionRepository()
    v_repo = VolumetryRepository()
    exp_repo = ExplosionRepository()

    hp = hp_repo.find_by_id(home_production_id)
    if not hp:
        return False

    current_lots = hp.get('lots', {})

    current_explosion = exp_repo.find_all({
        'home_production_id': home_production_id,
    }) or []

    volumetry = v_repo.find_all({
        "client_id": hp.get("client_id"),
        "front": hp.get("front"),
    }) or []

    if len(current_explosion) == 0:
        for v in volumetry:
            material_id = v.get("material_id")
            supplier_id = v.get("supplier_id")
            current_exp = exp_repo.find_one({
                "home_production_id": home_production_id,
                "material_id": material_id,
                "supplier_id": supplier_id,
            })
            if current_exp:
                amounts = update_amounts(current_exp, v, hp)
                gran_total = r2(sum(to_float(a.get("total", 0))
                                    for a in (amounts or [])))
                exp_repo.update(str(current_exp.get('_id')), {
                    "explosion": amounts,
                    "gran_total": gran_total,
                })
            else:
                amounts = create_amounts(v, hp)
                gran_total = r2(sum(to_float(a.get("total", 0))
                                for a in (amounts or [])))
                exp_repo.insert({
                    "home_production_id": home_production_id,
                    "material_id": material_id,
                    "supplier_id": supplier_id,
                    "explosion": amounts,
                    "gran_total": gran_total,
                    "status": 0,
                })
        invalidate_cache('explosion')
        return True

    merged = merge_explosion(current_explosion, volumetry)
    for e in merged:
        volumetry = e.get('volumetry')
        if volumetry:
            current_exp = exp_repo.find_one({
                "home_production_id": home_production_id,
                "material_id": e.get("material_id"),
                "supplier_id": e.get("supplier_id"),
            })
            if current_exp:
                amounts = update_amounts(current_exp, e, hp)
                gran_total = r2(sum(to_float(a.get("total", 0))
                                    for a in (amounts or [])))
                exp_repo.update(str(current_exp.get('_id')), {
                    "explosion": amounts,
                    "gran_total": gran_total,
                })
            else:
                amounts = create_amounts(e, hp)
                gran_total = r2(sum(to_float(a.get("total", 0))
                                for a in (amounts or [])))
                exp_repo.insert({
                    "home_production_id": home_production_id,
                    "material_id": e.get("material_id"),
                    "supplier_id": e.get("supplier_id"),
                    "explosion": amounts,
                    "gran_total": gran_total,
                    "status": 0,
                })
        else:
            new_exp = scale_explosion(
                e, prev_lots, int(current_lots.get('total', 0)))
            query_upsert = {
                "home_production_id": home_production_id,
                "material_id": e.get("material_id"),
                "supplier_id": e.get("supplier_id"),
            }
            set_data = {
                "explosion": new_exp.get('explosion', []),
                "gran_total": new_exp.get('gran_total', 0),
            }
            exp_repo.upsert_one(query_upsert, set_data)
    invalidate_cache('explosion')
    return True
