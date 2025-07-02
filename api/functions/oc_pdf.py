import os
from django.conf import settings
from datetime import datetime
from reportlab.lib.pagesizes import landscape, LETTER
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
)
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import Image
from reportlab.graphics.barcode import qr
from reportlab.graphics.shapes import Drawing
from reportlab.pdfbase.pdfmetrics import stringWidth
from api.helpers.format_str import clean_text


def format_items(items):
    result = []
    for item in items:
        row = [
            item.get('supplier_code', ''),
            item.get('color', ''),
            item.get('total_quantity', ''),
            item.get('concept', ''),
            item.get('measurement', ''),
            item.get('presentation', ''),
            item.get('inventory_price', ''),
            formato_moneda(item.get('total', ''))
        ]
        result.append(row)
    return result


def formato_moneda(valor, simbolo="$"):
    try:
        valor = float(valor)
        return f"{simbolo}{valor:,.2f}"
    except (ValueError, TypeError):
        return f"{simbolo}0.00"


def calcular_ancho_columna(data, font_name="Helvetica", font_size=7):
    num_cols = len(data[0])
    max_widths = [0] * num_cols

    for row in data:
        for i, cell in enumerate(row):
            text = str(cell)
            ancho = stringWidth(text, font_name, font_size)
            if ancho > max_widths[i]:
                max_widths[i] = ancho

    total = sum(max_widths)
    proporciones = [w / total for w in max_widths]
    return proporciones


def create_pdf(data):
    pdf_path = f'media/purchase_orders/pdf/OC{data['folio']}_{clean_text(data['client'])}_{clean_text(data['front'])}_OD{data['od']}_{clean_text(data['supplier_name'])}.pdf'
    os.makedirs(os.path.dirname(pdf_path), exist_ok=True)

    doc = SimpleDocTemplate(
        pdf_path,
        pagesize=landscape(LETTER),
        leftMargin=20 * mm,
        rightMargin=20 * mm,
        topMargin=15 * mm,
        bottomMargin=15 * mm
    )

    styles = getSampleStyleSheet()
    normal = ParagraphStyle(name="Normal", fontSize=9, leading=10)
    bold = ParagraphStyle(name="Bold", parent=normal,
                          fontName="Helvetica-Bold")
    right = ParagraphStyle(name="Right", parent=normal, alignment=2)

    content = []

    # TÍTULO
    logo_path = f"{settings.BASE_URL}/media/images/svg-logo-bellarti.png"
    qr_code = qr.QrCodeWidget(
        f"{settings.ADMIN_URL}purchase-orders/view/{str(data['_id'])}?input=true")
    width_qr = 40
    height_qr = 40
    d = Drawing(width_qr, height_qr)
    d.add(qr_code)

    try:
        logo = Image(logo_path, width=118, height=30)
    except Exception:
        logo = Paragraph("LOGO", styles["Normal"])

    encabezado_principal = Table(
        [[logo, Paragraph("<b>ORDEN DE COMPRA</b>", styles["Title"]), d]],
        colWidths=[doc.width * 0.2, doc.width * 0.6, doc.width * 0.2]
    )
    encabezado_principal.setStyle(TableStyle([
        ("ALIGN", (0, 0), (0, 0), "LEFT"),
        ("ALIGN", (1, 0), (1, 0), "CENTER"),
        ("ALIGN", (2, 0), (2, 0), "RIGHT"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE")
    ]))
    content.append(encabezado_principal)
    content.append(Spacer(1, 10))

    # ENCABEZADO EN 3 COLUMNAS
    encabezado_col1 = [
        ("ORDEN DE COMPRA:",
         f"#{data['folio']}-{datetime.now().strftime('%y')}"),
        ("CLIENTE:", data['client']),
        ("PROYECTO:", data['project']),
        ("FRENTE:", data['front']),
    ]
    encabezado_col2 = [
        ("PROVEEDOR:", data['supplier_name']),
        ("RFC:", data['rfc']),
        ("TELÉFONO:", data['phone']),
        ("EMAIL:", data['email']),
        ("DIRECCIÓN:", data['address']),
    ]
    encabezado_col3 = [
        ("FECHA:", data['created']),
        ("FECHA ESTIMADA DE ENTREGA:", data.get('estimated_delivery', 'S/D')),
        ("ESTATUS:", "APROBADA"),
    ]

    rows = max(len(encabezado_col1), len(
        encabezado_col2), len(encabezado_col3))
    for i in range(rows):
        fila = []
        for col, datos in zip(
            [encabezado_col1, encabezado_col2, encabezado_col3],
            [normal, normal, right]
        ):
            if i < len(col):
                k, v = col[i]
                fila.append(Paragraph(f"<b>{k}</b> {v}", datos))
            else:
                fila.append("")
        content.append(Table([fila], colWidths="*"))
    content.append(Spacer(1, 8))

    # ASUNTO Y PROTOTIPOS
    content.append(
        Paragraph(f"<b>ASUNTO:</b> {data.get('subject', '')}", normal))
    content.append(Spacer(1, 5))
    content.append(
        Paragraph(f"<b>PROTOTIPOS:</b> {' | '.join([f'{k} - {v}' for k, v in data['prototypes'].items()])}", normal))
    content.append(Spacer(1, 10))

    # TABLA DE PRODUCTOS
    headers = [
        "Clave Producto", "Color", "Cantidad", "Descripción",
        "Unidad", "Presentación", "P. Unitario", "Total"
    ]
    items = [headers] + format_items(data['items'])

    proporciones = calcular_ancho_columna(items, font_size=7)
    col_widths = [doc.width * p for p in proporciones]
    tabla = Table(items, colWidths=col_widths, repeatRows=1)
    tabla.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
        ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 7),
        ("ALIGN", (0, 0), (-2, -1), "LEFT"),
        ("ALIGN", (-2, 1), (-1, -1), "CENTER")
    ]))
    content.append(tabla)
    content.append(Spacer(1, 12))

    # TOTALES
    content.append(
        Paragraph(f"<b>SUBTOTAL:</b> {formato_moneda(data['subtotal'])}", right))
    content.append(
        Paragraph(f"<b>IVA:</b> {formato_moneda(data['iva'])}", right))
    content.append(
        Paragraph(f"<b>TOTAL:</b> {formato_moneda(data['total'])}", right))
    content.append(Spacer(1, 12))

    # OBSERVACIONES
    content.append(Paragraph("<b>OBSERVACIONES:</b>", bold))
    # Cuadro para observaciones (5 líneas)
    content.append(Table(
        [[""] * 1] * 3,
        colWidths=[doc.width],
        rowHeights=12,
        style=[("BOX", (0, 0), (-1, -1), 1, colors.black),
               ("GRID", (0, 0), (-1, -1), 0.25, colors.grey)]
    ))
    content.append(Spacer(1, 10))

    # LEYENDA
    content.append(Paragraph("<b>Este documento NO ES UNA FACTURA.</b>", bold))
    content.append(Spacer(1, 10))

    # LUGAR DE ENTREGA
    content.append(Paragraph("<b>LUGAR DE ENTREGA:</b>", bold))
    placeofdelivery_lines = [
        "Blvd Adolfo López Mateos #2607, Int.4, Col. Barrio de Guadaupe. CP.37289. León, Guanajuato.",
        "HORARIO DE RECEPCIÓN: 8AM A 1PM DE LUNES A VIERNES",
    ]
    for line in placeofdelivery_lines:
        content.append(Paragraph(line, normal))
    content.append(Spacer(1, 10))

    # FACTURACIÓN
    content.append(Paragraph("<b>FACTURACIÓN:</b>", bold))
    facturacion_lines = [
        "MÉTODO DE PAGO: TRANSFERENCIA",
        "FORMA DE PAGO: 1 EXHIBICIÓN",
        "USO DE CFD: ADQUISICIÓN DE MERCANCÍAS",
        "ENVIAR FACTURA A: facturas@bellarti.com.mx"
    ]
    for line in facturacion_lines:
        content.append(Paragraph(line, normal))
    content.append(Spacer(1, 10))

    # FIRMAS
    content.append(Paragraph("<b>AUTORIZADO POR</b>", bold))
    content.append(Spacer(1, 40))
    firmas = Table(
        [[
            Paragraph("DIRECCIÓN", bold),
            Paragraph("ARQ. EUGENIA REYNOSO", bold),
            Paragraph("DPTO. COMPRAS", bold)
        ]],
        colWidths=[doc.width / 3.0] * 3
    )
    firmas.setStyle(TableStyle([
        ("LINEABOVE", (0, 0), (-1, 0), 0.5, colors.black),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("TOPPADDING", (0, 0), (-1, -1), 12)
    ]))
    content.append(firmas)

    doc.build(content)

    return pdf_path
