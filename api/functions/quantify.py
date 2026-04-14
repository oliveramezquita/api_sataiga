from celery import shared_task
from typing import Any, Dict, List
from api.helpers.formats import to_float, normalize_strict
from api.constants import EQUIPMENTS, CARPENTRY, CATS
from api.repositories.volumetry_repository import VolumetryRepository
from api.repositories.material_repository import MaterialRepository
from api.repositories.quantification_repository import QuantificationRepository


EQUIPMENTS_NORM = {normalize_strict(e) for e in EQUIPMENTS}
CARPENTRY_NORM = {normalize_strict(c) for c in CARPENTRY}


def r2(x: float) -> float:
    return round(float(x or 0), 2)


@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=True, max_retries=5)
def quantify(self, client_id: str, front: str, prototype: str) -> bool:
    v_repo = VolumetryRepository()
    m_repo = MaterialRepository()
    q_repo = QuantificationRepository()

    # 1) Fuente de verdad: volumetría actual en DB
    volumetries = v_repo.find_all(
        query={"client_id": client_id, "front": front, "prototype": prototype},
        projection={"material_id": 1, "volumetry": 1},  # optimiza
    ) or []

    # 2) Map de materials por id (para división)
    material_ids = [v.get("material_id")
                    for v in volumetries if v.get("material_id")]
    mats = m_repo.find_many_by_ids(
        material_ids,
        projection={"division": 1},
        dedupe=True,
    ) or []
    materials_map = {str(m["_id"]): m for m in mats if isinstance(
        m, dict) and m.get("_id")}

    # 3) Estructura: recalcular desde cero (soporta delete)
    buckets: Dict[str, Dict[str, Dict[str, Any]]] = {cat: {} for cat in CATS}

    def upsert(cat: str, material_id: str, data_dict: Dict[str, Any], total: float) -> None:
        if total <= 0:
            # Si quieres mantener entradas con total 0, quita este if.
            return
        buckets[cat][material_id] = {
            "material_id": material_id,
            **data_dict,
            "TOTAL": r2(total),
        }

    # 4) Cálculo
    for item in volumetries:
        material_id = str(item.get("material_id") or "")
        if not material_id:
            continue

        rows: List[dict] = item.get("volumetry") or []
        mat = materials_map.get(material_id, {})
        division_norm = normalize_strict(mat.get("division") or "")

        # EQUIPOS (delivery por área)
        if division_norm in EQUIPMENTS_NORM:
            dlvy: Dict[str, float] = {}
            total_dlvy = 0.0

            for v in rows:
                area = v.get("area")
                delivery = to_float(v.get("delivery", 0), 0.0, min_value=0.0)
                if area:
                    dlvy[area] = r2(delivery)
                total_dlvy += delivery

            upsert("EQUIPOS", material_id, dlvy, total_dlvy)
            continue

        # CARPINTERÍA (factory+installation+delivery por área)
        if division_norm in CARPENTRY_NORM:
            carp: Dict[str, float] = {}
            total_carp = 0.0

            for v in rows:
                area = v.get("area")
                factory = to_float(v.get("factory", 0), 0.0, min_value=0.0)
                installation = to_float(
                    v.get("installation", 0), 0.0, min_value=0.0)
                delivery = to_float(v.get("delivery", 0), 0.0, min_value=0.0)

                qty = factory + installation + delivery
                if area:
                    carp[area] = r2(qty)
                total_carp += qty

            upsert("CARPINTERÍA", material_id, carp, total_carp)
            continue

        # OTROS (producción/instalación por área; entregas solo COCINA)
        prod: Dict[str, float] = {}
        inst: Dict[str, float] = {}
        dlvy: Dict[str, float] = {}

        total_prod = 0.0
        total_inst = 0.0
        total_dlvy = 0.0
        has_cocina = False

        for v in rows:
            area = v.get("area") or ""
            area_norm = normalize_strict(area)

            factory = to_float(v.get("factory", 0), 0.0, min_value=0.0)
            installation = to_float(
                v.get("installation", 0), 0.0, min_value=0.0)
            delivery = to_float(v.get("delivery", 0), 0.0, min_value=0.0)

            if area:
                prod[area] = r2(factory)
                inst[area] = r2(installation)

            total_prod += factory
            total_inst += installation

            if area_norm == "cocina":
                has_cocina = True
                dlvy[area] = r2(delivery)
                total_dlvy += delivery

        if has_cocina:
            upsert("PRODUCCIÓN SOLO COCINA", material_id, prod, total_prod)
            upsert("INSTALACIÓN SOLO COCINA", material_id, inst, total_inst)
            upsert("ENTREGAS COCINA", material_id, dlvy, total_dlvy)
        else:
            upsert("PRODUCCIÓN SIN COCINA", material_id, prod, total_prod)
            upsert("INSTALACIÓN SIN COCINA", material_id, inst, total_inst)

    # 5) Materializar a listas
    quantification = {cat: list(buckets[cat].values()) for cat in CATS}

    # 6) Upsert (llave natural)
    query = {"client_id": client_id, "front": front, "prototype": prototype}
    set_data = {**query, "quantification": quantification}
    q_repo.upsert_one(query, set_data)

    return True
