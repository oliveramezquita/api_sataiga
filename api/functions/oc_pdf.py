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
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from PyPDF2 import PdfReader, PdfWriter
from io import BytesIO
from reportlab.graphics.shapes import Drawing
from reportlab.graphics import renderPDF
from reportlab.graphics.barcode import qr
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT, TA_JUSTIFY


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


def generate_pdf():
    """Generate PDF test."""
    pdf_generator = PDFGenerator(
        template='media/templates/purchaseorder_template.pdf',
        output_path='media/purchase_orders/pdf/purchase_order.pdf'
    )
    purchaseorder_id = '1104-OD990'
    pdf_generator.add_wrap_text(30, 70, 220,
                                ["NORMA PATRICIA RODRÍGUEZ RODRÍGUEZ",
                                 "RFC: RORN770318IQ1",
                                 "BLVD. ADOLFO LOPEZ MATEOS #2607 INT. 4D. COL. BARRIO DE GUADALUPE",
                                 "CP. 37289 LEÓN, GTO.",
                                 "facturas@bellarti.com.mx"],
                                )
    pdf_generator.add_wrap_text(250, 71, 220, ["12/05/2025"])
    pdf_generator.add_wrap_text(
        250, 96, 220, [purchaseorder_id], font_color='white')
    pdf_generator.add_wrap_text(
        250, 122, 220, ["S3- 4 PIAMONTE, 2 VENETO"], font_color='white')
    pdf_generator.add_wrap_text(250, 155, 220, ["HERRAJES"])
    data_table = [
        ["NOMBRE:", "CERRAJES DE MEXICO SA DE DV"],
        ["RFC:", "CME971020753"],
        ["DIRECCIÓN:", "AV. PEÑUELAS 3-1 FRACC. IND SAN PEDRITO PEÑUELAS SANTIAGO, QRO."],
        ["CP:", "45678"],
        ["EMAIL:", "mramirez@cerrajes.com"],
        ["TELÉFONO:", "477-151-0674"],
    ]
    pdf_generator.add_table(29, 130, data_table, col_widths=[
                            50, 170], font_size=7)
    pdf_generator.add_qr_code(
        data=f"{settings.ADMIN_URL}purchase-orders/view/{purchaseorder_id}?input=true",
        coord_x=485,
        coord_y=105,
        size=80
    )
    materials_table = [
        ["0601-368", "Encino Polar / Alto Brillo - Granito San Gabriel", "12", 'Soporte frontal derecho para corredera Cerrajes "Impaz" niquelado con taquete de Ø=10mm',
            "Pza", "$45.00", "$540.00"],
        ["1102-004", "Encino Polar / Alto Brillo - Granito San Gabriel", "5",
            'Tornillo fijación de herrajes cabeza plana “Gripper” #6 x5/8″ (15,875 mm) PH2 Niquelado con punta', "Pza", "$30.00", "$150.00"],
        ["0601-368", "Encino Polar / Alto Brillo - Granito San Gabriel", "12", 'Soporte frontal derecho para corredera Cerrajes "Impaz" niquelado con taquete de Ø=10mm',
            "Pza", "$45.00", "$540.00"],
        ["1102-004", "Encino Polar / Alto Brillo - Granito San Gabriel", "5",
            'Tornillo fijación de herrajes cabeza plana “Gripper” #6 x5/8″ (15,875 mm) PH2 Niquelado con punta', "Pza", "$30.00", "$150.00"],
        ["0601-368", "Encino Polar / Alto Brillo - Granito San Gabriel", "12", 'Soporte frontal derecho para corredera Cerrajes "Impaz" niquelado con taquete de Ø=10mm',
            "Pza", "$45.00", "$540.00"],
        ["1102-004", "Encino Polar / Alto Brillo - Granito San Gabriel", "5",
            'Tornillo fijación de herrajes cabeza plana “Gripper” #6 x5/8″ (15,875 mm) PH2 Niquelado con punta', "Pza", "$30.00", "$150.00"],
    ]
    col_widths = [70, 94, 50, 170, 50, 60, 60]
    next_y = pdf_generator.add_materials_table(
        coord_x=29,
        coord_y=235,
        data=materials_table,
        col_widths=col_widths,
        font_size=7.5
    )
    pdf_generator.add_wrap_text(
        coord_x=101,
        coord_y=next_y,
        width=300,
        content=["OBSERVACIONES:"],
        font_color='gray'
    )
    label_tabla = [
        ["Subtotal:"],
        ["(-) % Descuento"],
        ["(+) IVA 16%:"]
    ]
    pdf_generator.add_table(463, next_y-18, label_tabla,
                            col_widths=[59], font_size=7.5, background_color='#f5f5f5',
                            background_cols=[0])
    subtotal_tabla = [
        ["$ 53,005.48"],
        ["-"],
        ["$ 8,480.88"]
    ]
    pdf_generator.add_table(522, next_y-18, subtotal_tabla,
                            col_widths=[59], font_size=7.5, show_grid=True, align='RIGHT')
    total_tabla_label = [["TOTAL"]]
    pdf_generator.add_table(463, next_y+30, total_tabla_label,
                            col_widths=[59], font_size=7.5, background_color='gray',
                            background_cols=[0], show_grid=True, font_name='Arial Italic', align='CENTER', text_color='white')
    total_table = [["$ 61,486.36"]]
    pdf_generator.add_table(522, next_y+30, total_table,
                            col_widths=[59], font_size=7.5, show_grid=True, align='RIGHT', font_name='Arial Italic')
    pdf_generator.add_line(
        coord_x=101,
        coord_y=next_y,
        line_width=314,
        line_spacing=12,
        lines=3,
        line_color='gray',
        line_border=0.5
    )
    pdf_generator.add_wrap_text(
        coord_x=101,
        coord_y=next_y+50,
        width=314,
        content=["Este documento NO ES UNA FACTURA."],
        font_name='Arial Italic',
        font_color='gray'
    )
    pdf_generator.add_line(
        coord_x=29,
        coord_y=next_y+55,
        line_width=554,
        line_spacing=12,
        line_border=0.5
    )
    billing_table = [
        ["FACTURACIÓN:", "MÉTODO DE PAGO: POR DEFINIR"],
        ["", "FORMA DE PAGO: PPD (PAGO EN PARCIALIDADES)"],
        ["", "USO DE CFD: ADQUISICIÓN DE MERCANCÍAS"],
        ["", "ENVIAR FACTURA A: facturas@bellarti.com.mx"]
    ]
    pdf_generator.add_table(29, next_y+60, billing_table,
                            col_widths=[164, 220], font_size=7.5)
    pdf_generator.add_line(
        coord_x=29,
        coord_y=next_y+115,
        line_width=554,
        line_spacing=12,
        line_border=0.5
    )
    pdf_generator.add_wrap_text(
        coord_x=29,
        coord_y=next_y+140,
        width=164,
        content=["AUTORIZADO POR:"],
        font_size=7.5
    )
    pdf_generator.add_line(
        coord_x=29,
        coord_y=next_y+174,
        line_width=160,
        line_spacing=12,
        line_border=0.5
    )
    pdf_generator.add_line(
        coord_x=226,
        coord_y=next_y+174,
        line_width=160,
        line_spacing=12,
        line_border=0.5
    )
    pdf_generator.add_line(
        coord_x=423,
        coord_y=next_y+174,
        line_width=160,
        line_spacing=12,
        line_border=0.5
    )
    signs_table = [
        ["DIRECCIÓN", "ARQ. EUGENIA REYNOSO", "DPTO. COMPRAS"]
    ]
    pdf_generator.add_table(29, next_y+182, signs_table,
                            col_widths=[160, 234, 160], font_size=7.5, align='CENTER')
    pdf_generator.generate()


def wrap_text(text, font_name, font_size, max_width):
    lines = []
    paragraphs = text.split('\n')

    for idx, paragraph in enumerate(paragraphs):
        words = paragraph.split()
        current_line = ""

        for word in words:
            test_line = f"{current_line} {word}".strip()
            if pdfmetrics.stringWidth(test_line, font_name, font_size) <= max_width:
                current_line = test_line
            else:
                lines.append(current_line)
                current_line = word

        if current_line:
            lines.append(current_line)

        if idx < len(paragraphs) - 1:
            lines.append("")

    return [line for line in lines if line]


class PDFGenerator:
    def __init__(self, template, output_path):
        pdfmetrics.registerFont(TTFont('Arial', 'media/fonts/Arial.ttf'))
        pdfmetrics.registerFont(
            TTFont('Arial Italic', 'media/fonts/ArialItalic.ttf'))
        self.buffer = BytesIO()
        self.c = canvas.Canvas(self.buffer, pagesize=letter)
        _, self.height = letter
        self.template = template
        self.output_path = output_path

    def add_wrap_text(self, coord_x, coord_y, width, content, **kwargs):
        text = "\n".join(content)
        x = coord_x
        y = self.height - coord_y
        max_width = width
        font_name = kwargs.get('font_name', 'Arial')
        font_size = kwargs.get('font_size', 8)
        font_color = kwargs.get('font_color', colors.black)

        if isinstance(font_color, str):
            font_color = getattr(colors, font_color.lower(), colors.black)

        lines = wrap_text(text, font_name, font_size, max_width)

        text_obj = self.c.beginText()
        text_obj.setTextOrigin(x, y)
        text_obj.setFont(font_name, font_size)
        text_obj.setFillColor(font_color)

        for line in lines:
            text_obj.textLine(line)

        self.c.drawText(text_obj)

    def add_table(self, coord_x, coord_y, data, col_widths=None, row_height=15, **kwargs):
        font_name = kwargs.get('font_name', 'Arial')
        font_size = kwargs.get('font_size', 8)
        show_grid = kwargs.get('show_grid', False)
        background_color = kwargs.get(
            'background_color')          # Puede ser None
        background_rows = kwargs.get('background_rows', [])
        background_cols = kwargs.get('background_cols', [])
        text_color = kwargs.get('text_color', colors.black)
        align = kwargs.get('align', 'LEFT')

        ALIGN_MAP = {
            'LEFT': TA_LEFT,
            'CENTER': TA_CENTER,
            'RIGHT': TA_RIGHT,
            'JUSTIFY': TA_JUSTIFY,
        }

        style_paragraph = ParagraphStyle(
            name="TableCell",
            fontName=font_name,
            fontSize=font_size,
            textColor=text_color,
            alignment=ALIGN_MAP.get(align.upper(), TA_LEFT),
            leading=font_size + 2,
        )

        wrapped_data = []
        for row in data:
            wrapped_row = [
                Paragraph(str(cell or ''), style_paragraph) for cell in row
            ]
            wrapped_data.append(wrapped_row)

        y = self.height - coord_y
        table = Table(wrapped_data, colWidths=col_widths)

        style = TableStyle([
            ('FONT', (0, 0), (-1, -1), font_name, font_size),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 1),
            ('RIGHTPADDING', (0, 0), (-1, -1), 1),
            ('TOPPADDING', (0, 0), (-1, -1), 1),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 1),
        ])

        # Fondo por fila
        for row_idx in background_rows:
            style.add('BACKGROUND', (0, row_idx),
                      (-1, row_idx), background_color)

        # Fondo por columna
        for col_idx in background_cols:
            style.add('BACKGROUND', (col_idx, 0),
                      (col_idx, len(data) - 1), background_color)

        if show_grid:
            style.add('GRID', (0, 0), (-1, -1), 0.5, colors.black)

        table.setStyle(style)

        table.wrapOn(self.c, 0, 0)
        table.drawOn(self.c, coord_x, y - row_height * len(data))

    def add_materials_table(self, coord_x, coord_y, data, col_widths=None, **kwargs):
        font_name = kwargs.get('font_name', 'Arial')
        font_size = kwargs.get('font_size', 8)

        headers = [
            "Clave del Producto", "Color", "Cantidad", "Descripción",
            "Unidad", "P. Unitario", "Total"
        ]
        all_rows = [headers] + data

        # Estilos por columna
        paragraph_styles = []
        for i in range(7):  # 7 columnas
            alignment = 'CENTER' if i < 5 else 'RIGHT'
            paragraph_styles.append(ParagraphStyle(
                name=f"Col{i}",
                fontName=font_name,
                fontSize=font_size,
                leading=font_size + 2,
                alignment={'LEFT': 0, 'CENTER': 1, 'RIGHT': 2}[alignment]
            ))

        wrapped_data = []
        for row in all_rows:
            wrapped_row = []
            for col_idx, cell in enumerate(row):
                value = str(cell or '')
                # Formatear valores monetarios
                if row != headers and col_idx in [5, 6]:
                    try:
                        number = float(str(cell).replace(
                            '$', '').replace(',', ''))
                        value = f"${number:,.2f}"
                    except (ValueError, TypeError):
                        pass
                wrapped_row.append(Paragraph(value, paragraph_styles[col_idx]))
            wrapped_data.append(wrapped_row)

        table = Table(wrapped_data, colWidths=col_widths)
        num_rows = len(wrapped_data)

        style = TableStyle()
        style.add('FONT', (0, 0), (-1, -1), font_name, font_size)
        style.add('GRID', (0, 0), (-1, -1), 0.5, colors.black)
        style.add('VALIGN', (0, 0), (-1, -1), 'MIDDLE')
        style.add('LEFTPADDING', (0, 0), (-1, -1), 2)
        style.add('RIGHTPADDING', (0, 0), (-1, -1), 2)

        # Alineación por columnas
        style.add('ALIGN', (0, 0), (4, -1), 'CENTER')  # columnas 0 a 4
        style.add('ALIGN', (5, 0), (6, -1), 'RIGHT')    # columnas 5 y 6

        # Cabecera
        style.add('BACKGROUND', (0, 0), (-1, 0), colors.darkgrey)
        style.add('TEXTCOLOR', (0, 0), (-1, 0), colors.white)

        # Columna Total (col 6), desde fila 1 a última
        style.add('BACKGROUND', (6, 1), (6, num_rows - 1), colors.lightgrey)

        table.setStyle(style)

        # Punto de partida desde arriba
        y_top = self.height - coord_y  # coord_y es desde arriba

        # Medir la altura real que usará la tabla
        _, table_height = table.wrap(0, 0)

        # Dibuja la tabla (ajustada desde la parte superior hacia abajo)
        table.drawOn(self.c, coord_x, y_top - table_height)

        # Retorna el punto exacto justo debajo de la tabla (coordenada desde arriba)
        # <-- lo que sigue se coloca más abajo desde la parte superior
        return coord_y + table_height + 15

    def add_qr_code(self, data, coord_x, coord_y, size=100):
        qr_code = qr.QrCodeWidget(data)
        bounds = qr_code.getBounds()
        width = bounds[2] - bounds[0]
        height = bounds[3] - bounds[1]

        d = Drawing(size, size, transform=[
                    size / width, 0, 0, size / height, 0, 0])
        d.add(qr_code)

        y = self.height - coord_y  # ajustar desde parte superior
        renderPDF.draw(d, self.c, coord_x, y - size)

    def add_line(self, coord_x, coord_y, line_width=500, line_spacing=20, **kwargs):
        lines = kwargs.get('lines', 1)
        line_color = kwargs.get('line_color', 'black')
        line_border = kwargs.get('line_border', 1)
        y = self.height - coord_y

        self.c.setStrokeColor(line_color)
        self.c.setLineWidth(line_border)

        for i in range(lines):
            line_y = y - (i + 1) * line_spacing
            self.c.line(coord_x, line_y, coord_x + line_width, line_y)

    def generate(self):
        self.c.save()
        self.buffer.seek(0)

        template = PdfReader(self.template)
        overlay = PdfReader(self.buffer)
        writer = PdfWriter()

        page = template.pages[0]
        page.merge_page(overlay.pages[0])
        writer.add_page(page)

        with open(self.output_path, "wb") as f:
            writer.write(f)
