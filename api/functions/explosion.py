from celery import shared_task
from typing import Any, Dict, List

from api.utils.cache_utils import invalidate_cache
from api.helpers.formats import to_float
from api.repositories.home_production_repository import HomeProductionRepository
from api.repositories.volumetry_repository import VolumetryRepository
from api.repositories.explosion_repository import ExplosionRepository


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


def remove_prototype(area: Dict[str, Any], prototype: str) -> Dict[str, Any]:
    area["prototypes"] = [p for p in (
        area.get("prototypes") or []) if p.get("prototype") != prototype]
    area["total"] = total_from_prototypes(area["prototypes"])
    return area


def update_by_area(explosion: List[Dict[str, Any]], area_name: str, new_entry: Dict[str, Any]) -> List[Dict[str, Any]]:
    for i, d in enumerate(explosion or []):
        if d.get("area") == area_name:
            explosion[i] = new_entry
            return explosion
    return explosion


def takeout_amounts(item: Dict[str, Any], hp: Dict[str, Any]) -> List[Dict[str, Any]]:
    explosion_repo = ExplosionRepository()

    lots_prototypes = (hp.get("lots") or {}).get("prototypes") or {}
    prototype = item.get("prototype")

    explosion_docs = explosion_repo.find_all({
        "home_production_id": str(hp["_id"]),
        "material_id": item.get("material_id"),
        "supplier_id": item.get("supplier_id"),
    }) or []

    # Si el prototype no está contemplado en lots, no hay nada que mover
    if not prototype or prototype not in lots_prototypes:
        return explosion_docs[0].get("explosion", []) if explosion_docs else []

    multiplier = to_float(lots_prototypes.get(
        prototype, 0), 0.0, min_value=0.0)

    # ---- Caso SIN documento previo ----
    if not explosion_docs:
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

    # ---- Caso CON documento previo ----
    areas = explosion_docs[0].get("explosion", []) or []

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

        exp = next((d for d in areas if d.get("area") == area), None)

        if exp:
            # 1) Quitar si existía ese prototype
            exp = remove_prototype(exp, prototype)

            # 2) Agregarlo si hay valores
            if total > 0:
                exp["prototypes"].append({
                    "prototype": prototype,
                    "quantities": {
                        "factory": factory,
                        "installation": installation,
                        "delivery": delivery,
                    },
                })

            # 3) Total del área = suma de TODOS los prototypes (no solo el actual)
            exp["total"] = total_from_prototypes(exp.get("prototypes") or [])

            areas = update_by_area(areas, area, exp)

        else:
            if total > 0:
                prototypes = [{
                    "prototype": prototype,
                    "quantities": {
                        "factory": factory,
                        "installation": installation,
                        "delivery": delivery,
                    },
                }]
                areas.append({
                    "area": area,
                    "prototypes": prototypes,
                    "total": total_from_prototypes(prototypes),
                })

    return areas


@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=True, max_retries=5)
def explosion(self, home_production_id: str):
    hp_repo = HomeProductionRepository()
    v_repo = VolumetryRepository()
    exp_repo = ExplosionRepository()

    hp = hp_repo.find_by_id(home_production_id)
    if not hp:
        return False

    # Recomendación: filtra por prototype si aplica en tu negocio
    query = {
        "client_id": hp.get("client_id"),
        "front": hp.get("front"),
    }
    volumetry = v_repo.find_all(query) or []

    for v in volumetry:
        amounts = takeout_amounts(v, hp)
        gran_total = r2(sum(to_float(a.get("total", 0))
                        for a in (amounts or [])))

        query_upsert = {
            "home_production_id": home_production_id,
            "material_id": v.get("material_id"),
            "supplier_id": v.get("supplier_id"),
        }

        set_data = {
            **query_upsert,
            "explosion": amounts,
            "gran_total": gran_total,
            "status": 0,
        }

        exp_repo.upsert_one(query_upsert, set_data)
        invalidate_cache('explosion')

    return True
