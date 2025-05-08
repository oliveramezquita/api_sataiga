from copy import deepcopy
from api_sataiga.handlers.mongodb_handler import MongoDBHandler
from api.serializers.volumetry_serializer import VolumetrySerializer
from celery import shared_task


def get_volumetry(client_id, front):
    with MongoDBHandler('volumetries') as db:
        volumetry = db.extract({'client_id': client_id, 'front': front})
        if volumetry:
            return VolumetrySerializer(volumetry, many=True).data
        return []


def convert_to_float(valor):
    try:
        return round(float(valor), 2)
    except ValueError:
        return 0.00


@shared_task
def quantify(client_id, front):
    with MongoDBHandler('quantification') as db:
        volumetry = get_volumetry(client_id, front)
        prototypes_set = set()

        for item in volumetry:
            for v in item["volumetry"]:
                for p in v["prototypes"]:
                    prototypes_set.add(p["prototype"])

        for prototype in prototypes_set:
            quantification = db.extract({
                'client_id': client_id,
                'front': front,
                'prototype': prototype})
            result = {
                "prototype": prototype,
                "front": volumetry[0]["front"],
                "client_id": volumetry[0]["client_id"],
                "quantification": {
                    "PRODUCCION SOLO COCINA": [],
                    "PRODUCCION SIN COCINA": [],
                    "INSTALACION SOLO COCINA": [],
                    "INSTALACION SIN COCINA": [],
                    "CARPINTERIA": [],
                    "EQUIPOS": [],
                }
            }

            for item in volumetry:
                material_info = {
                    "material_id": item.get("material_id", item.get("_id")),
                    "material": deepcopy(item["material"])
                }

                prod_cocina = {}
                prod_sin_cocina = {}
                inst_cocina = {}
                inst_sin_cocina = {}

                total_prod = 0
                total_inst = 0

                for v in item["volumetry"]:
                    for p in v["prototypes"]:
                        if p["prototype"] != prototype:
                            continue

                        factory = convert_to_float(p["quantities"]["factory"])
                        instalation = convert_to_float(
                            p["quantities"]["instalation"])

                        if v["area"] == "COCINA":
                            prod_cocina[v["area"]] = factory
                            inst_cocina[v["area"]] = instalation
                        else:
                            prod_sin_cocina[v["area"]] = factory
                            inst_sin_cocina[v["area"]] = instalation
                            total_prod += factory
                            total_inst += instalation

                if prod_sin_cocina:
                    data = deepcopy(material_info)
                    data.update(prod_sin_cocina)
                    data["TOTAL"] = total_prod
                    result["quantification"]["PRODUCCION SIN COCINA"].append(
                        data)

                if prod_cocina:
                    data = deepcopy(material_info)
                    data.update(prod_cocina)
                    result["quantification"]["PRODUCCION SOLO COCINA"].append(
                        data)

                if inst_sin_cocina:
                    data = deepcopy(material_info)
                    data.update(inst_sin_cocina)
                    data["TOTAL"] = total_inst
                    result["quantification"]["INSTALACION SIN COCINA"].append(
                        data)

                if inst_cocina:
                    data = deepcopy(material_info)
                    data.update(inst_cocina)
                    result["quantification"]["INSTALACION SOLO COCINA"].append(
                        data)

            if quantification:
                db.update({
                    'client_id': client_id,
                    'front': front,
                    'prototype': prototype}, {'quantification': result["quantification"]})
            else:
                db.insert(result)
