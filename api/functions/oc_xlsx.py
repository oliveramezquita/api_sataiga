from api.helpers.format_str import clean_text
from openpyxl import Workbook
from datetime import datetime


def create_xlsx(data):
    wb = Workbook()
    ws = wb.active
    ws.title = "ORDEN DE COMPRA"

    ws.append(["ORDEN DE COMPRA", f"{data['folio']}-{datetime.now().strftime('%y')}", None, "FECHA", data['created'],
               None, "FECHA ESTIMADA DE ENTREGA", data['estimated_delivery']])
    ws.append(["CLIENTE", data['client'], None, None,
               None, "ESTATUS", "APROBADA"])
    ws.append(["PROYECTO", data['project']])
    ws.append(["FRENTE", data['front'], "OD", data['od'],
               None, "PROVEEDOR", data['supplier_name']])
    ws.append([None, None, None, None, None,
               "RFC", data['rfc']])
    ws.append(["ASUNTO", None, None, None, None,
               "DIRECCIÓN", data['address']])
    ws.append([data['subject'], None, None, None, None,
               "TELÉFONO", data['phone']])
    ws.append([None, None, None, None, None,
               "EMAIL", data['email']])
    ws.append(["PROTOTIPOS:"])
    prototypes = data.get("prototypes", {})
    ws.append(list(prototypes.keys()))
    ws.append(list(prototypes.values()))
    ws.append([])

    header = ["MATERIAL", "CÓDIGO DE PROVEEDOR", "UNIDAD DE MEDIDA",
              "PRESENTACIÓN", "REFERENCIA", "CANTIDAD", "PRECIO", "TOTAL"]
    ws.append(header)

    for item in data['items']:
        ws.append([
            item["name"],
            item.get("supplier_code", None),
            item["measurement"],
            item.get("presentation", None),
            item.get("reference", None),
            round(float(item["total_quantity"]), 2),
            round(float(item["inventory_price"]), 2),
            round(float(item["total"]), 2)
        ])

    name = f'media/purchase_orders/excel/OC{data['folio']}_{clean_text(data['client'])}_{clean_text(data['front'])}_OD{data['od']}_{clean_text(data['supplier_name'])}.xlsx'
    wb.save(name)
    return name
