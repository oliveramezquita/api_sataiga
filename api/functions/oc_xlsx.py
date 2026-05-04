from pathlib import Path

from django.conf import settings
from openpyxl import Workbook

from api.helpers.formats import clean_text


def create_xlsx(data):
    wb = Workbook()
    ws = wb.active
    ws.title = "ORDEN DE COMPRA"

    supplier = data.get("supplier", {})

    ws.append([
        "ORDEN DE COMPRA", data.get("number", ""),
        None, "FECHA", data.get("created", ""),
        None, "FECHA ESTIMADA DE ENTREGA", data.get("estimated_delivery", "")
    ])

    ws.append([
        "CLIENTE", data.get("client", ""),
        None, None, None,
        "ESTATUS", "APROBADA"
    ])

    ws.append(["PROYECTO", data.get("project", "")])

    ws.append([
        "FRENTE", data.get("front", ""),
        "OD", data.get("od", ""),
        None, "PROVEEDOR", supplier.get("name", "")
    ])

    ws.append([None, None, None, None, None, "RFC", supplier.get("rfc", "")])
    ws.append(["ASUNTO", None, None, None, None,
              "DIRECCIÓN", supplier.get("address", "")])
    ws.append([data.get("subject", ""), None, None, None,
              None, "TELÉFONO", supplier.get("phone", "")])
    ws.append([None, None, None, None, None,
              "EMAIL", supplier.get("email", "")])

    ws.append(["PROTOTIPOS:"])

    prototypes = data.get("prototypes", {})
    if isinstance(prototypes, dict) and prototypes:
        ws.append(list(prototypes.keys()))
        ws.append(list(prototypes.values()))

    ws.append([])

    ws.append([
        "CLAVE DEL PRODUCTO",
        "COLOR",
        "CANTIDAD",
        "DESCRIPCIÓN",
        "UNIDAD DE MEDIDA",
        "P. UNITARIO",
        "TOTAL"
    ])

    for item in data.get("items", []):
        ws.append([
            item.get("supplier_code", ""),
            item.get("color", ""),
            round(float(item.get("total_quantity", 0)), 2),
            item.get("concept", ""),
            item.get("measurement", ""),
            round(float(item.get("inventory_price", 0)), 2),
            round(float(item.get("total", 0)), 2),
        ])

    folder = Path(settings.MEDIA_ROOT) / "purchase_orders" / "excel"
    folder.mkdir(parents=True, exist_ok=True)

    filename = (
        f"OC_{clean_text(data.get('client', 'cliente'))}_"
        f"{data.get('number', '')}_"
        f"{clean_text(supplier.get('name', 'proveedor'))}.xlsx"
    )

    path = folder / filename
    wb.save(path)

    relative_path = path.relative_to(settings.MEDIA_ROOT)
    return str(relative_path)
