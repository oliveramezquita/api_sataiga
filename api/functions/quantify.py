import re
from copy import deepcopy
from api_sataiga.handlers.mongodb_handler import MongoDBHandler
from celery import shared_task


def convert_to_float(valor):
    try:
        return round(float(valor), 2)
    except (ValueError, TypeError):
        return 0.00


@shared_task
def quantify(client_id, front, prototype, volumetry):
    with MongoDBHandler('quantification') as db:
        real_prototype = re.sub(r"\s*Cocina$", "", prototype)
        equipments = {'Campana', 'Estufa', 'Horno', 'Parrilla',
                      'Hielera', 'Microondas', 'Campana + Parrilla'}
        carpentry = {'Acabado', 'Herraje',
                     'Maderas', 'Resurtido', 'Tornillería'}

        quantification = db.extract({
            'client_id': client_id,
            'front': front,
            'prototype': real_prototype
        })

        if quantification and isinstance(quantification[0], dict):
            quant_data = quantification[0].get("quantification", {})
        else:
            quant_data = {}

        result = {
            "prototype": real_prototype,
            "front": front,
            "client_id": client_id,
            "quantification": {
                "PRODUCCIÓN SOLO COCINA": quant_data.get("PRODUCCIÓN SOLO COCINA", []),
                "PRODUCCIÓN SIN COCINA": quant_data.get("PRODUCCIÓN SIN COCINA", []),
                "INSTALACIÓN SOLO COCINA": quant_data.get("INSTALACIÓN SOLO COCINA", []),
                "INSTALACIÓN SIN COCINA": quant_data.get("INSTALACIÓN SIN COCINA", []),
                "ENTREGAS COCINA": quant_data.get("ENTREGAS COCINA", []),
                "CARPINTERÍA": quant_data.get("CARPINTERÍA", []),
                "EQUIPOS": quant_data.get("EQUIPOS", []),
            }
        }

        is_cocina = prototype.strip().endswith("Cocina")

        def add_entry(category, base_info, data_dict, total):
            if total > 0 and data_dict:
                data = deepcopy(base_info)
                data.update(data_dict)
                data["TOTAL"] = total

                existing = next(
                    (entry for entry in result["quantification"][category]
                     if entry["material_id"] == data["material_id"]),
                    None
                )

                if existing:
                    existing.clear()
                    existing.update(data)
                else:
                    result["quantification"][category].append(data)

        for item in volumetry:
            material_info = {"material_id": item['material_id']}

            if item['material']['division'] in equipments:
                dlvy = {}
                total_dlvy = 0
                for v in item["volumetry"]:
                    delivery = convert_to_float(v.get("delivery", 0))
                    dlvy[v["area"]] = delivery
                    total_dlvy += delivery
                add_entry("EQUIPOS", material_info, dlvy, total_dlvy)

            elif item['material']['division'] in carpentry:
                carp_data = {}
                total_carp = 0
                for v in item["volumetry"]:
                    factory = convert_to_float(v.get("factory", 0))
                    installation = convert_to_float(v.get("installation", 0))
                    delivery = convert_to_float(v.get("delivery", 0))

                    carp_data[v["area"]] = factory + installation + delivery
                    total_carp += carp_data[v["area"]]

                add_entry("CARPINTERÍA", material_info, carp_data, total_carp)

            else:
                prod, inst, dlvy = {}, {}, {}
                total_prod = total_inst = total_dlvy = 0

                for v in item["volumetry"]:
                    factory = convert_to_float(v.get("factory", 0))
                    installation = convert_to_float(v.get("installation", 0))
                    delivery = convert_to_float(v.get("delivery", 0))

                    if is_cocina:
                        prod[v["area"]] = factory
                        inst[v["area"]] = installation
                        dlvy[v["area"]] = delivery
                    else:
                        prod[v["area"]] = factory
                        inst[v["area"]] = installation

                    total_prod += factory
                    total_inst += installation
                    total_dlvy += delivery

                if is_cocina:
                    add_entry("PRODUCCIÓN SOLO COCINA",
                              material_info, prod, total_prod)
                    add_entry("INSTALACIÓN SOLO COCINA",
                              material_info, inst, total_inst)
                    add_entry("ENTREGAS COCINA",
                              material_info, dlvy, total_dlvy)
                else:
                    add_entry("PRODUCCIÓN SIN COCINA",
                              material_info, prod, total_prod)
                    add_entry("INSTALACIÓN SIN COCINA",
                              material_info, inst, total_inst)

        if quantification:
            db.update(
                {
                    'client_id': client_id,
                    'front': front,
                    'prototype': real_prototype
                },
                {'quantification': result["quantification"]}
            )
        else:
            db.insert(result)
