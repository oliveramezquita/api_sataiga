from api.helpers.format_str import clean_text
from openpyxl import Workbook


def create_xlsx(data):
    wb = Workbook()
    ws = wb.active
    ws.title = "ORDEN DE COMPRA"

    ws.append(["ORDEN DE COMPRA", f"{data['number']}", None, "FECHA", data['created'],
               None, "FECHA ESTIMADA DE ENTREGA", data['estimated_delivery']])
    ws.append(["CLIENTE", data['client'], None, None,
               None, "ESTATUS", "APROBADA"])
    ws.append(["PROYECTO", data['project']])
    ws.append(["FRENTE", data['front'], "OD", data['od'],
               None, "PROVEEDOR", data['supplier']['name']])
    ws.append([None, None, None, None, None,
               "RFC", data['supplier'].get('rfc', '')])
    ws.append(["ASUNTO", None, None, None, None,
               "DIRECCIÓN", data['supplier'].get('address', '')])
    ws.append([data['subject'], None, None, None, None,
               "TELÉFONO", data['supplier'].get('phone', '')])
    ws.append([None, None, None, None, None,
               "EMAIL", data['supplier'].get('email', '')])
    ws.append(["PROTOTIPOS:"])
    prototypes = data.get("prototypes", {})
    if isinstance(prototypes, dict):
        ws.append(list(prototypes.keys()))
        ws.append(list(prototypes.values()))
    ws.append([])

    header = ["CLAVE DEL PRODUCTO", "COLOR", "CANTIDAD",
              "DESCRIPCIÓN", "UNIDAD DE MEDIDA", "P. UNITARIO", "TOTAL"]
    ws.append(header)

    for item in data['items']:
        ws.append([
            item.get("supplier_code", None),
            item.get("color", None),
            round(float(item["total_quantity"]), 2),
            item["concept"],
            item["measurement"],
            round(float(item["inventory_price"]), 2),
            round(float(item["total"]), 2)
        ])

    name = f'media/purchase_orders/excel/OC_{clean_text(data['client'])}_{clean_text(data['number'])}_{clean_text(data['supplier']['name'])}.xlsx'
    wb.save(name)
    return name
