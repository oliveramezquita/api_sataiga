from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.platypus import Table, TableStyle, Paragraph
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT, TA_JUSTIFY
from reportlab.graphics.barcode import qr
from reportlab.graphics.shapes import Drawing
from reportlab.graphics import renderPDF
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from PyPDF2 import PdfReader, PdfWriter
from io import BytesIO


class PDFGenerator:
    def __init__(self, template, output_path, purchase_order_id):
        pdfmetrics.registerFont(TTFont('Arial', 'media/fonts/Arial.ttf'))
        pdfmetrics.registerFont(
            TTFont('Arial Italic', 'media/fonts/ArialItalic.ttf'))
        self.buffer = BytesIO()
        self.c = canvas.Canvas(self.buffer, pagesize=letter)
        self.width, self.height = letter
        self.template = template
        self.output_path = output_path
        self.page_height = letter[1]
        self.page_margin = 235  # margen superior e inferior
        self.y_cursor = self.page_height - self.page_margin
        self.current_page_index = 0
        self.is_new_page = False
        self.purchase_order_id = purchase_order_id

    def _wrap_text(self, text, font_name, font_size, max_width):
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

    def _add_page(self, margin_top=None):
        self.c.showPage()
        self.c.setFont("Arial", 8)
        self.current_page_index += 1

        if margin_top is None:
            # Margen inferior para siguientes páginas
            margin_top = 50 if self.current_page_index > 0 else self.page_margin

        self.y_cursor = self.page_height - margin_top
        self.is_new_page = True

    def _add_footer(self, page_num, total_pages):
        self.c.setFont("Arial", 8)
        footer_text = f"NÚM. ORDEN: {self.purchase_order_id} | PÁGINA {page_num} DE {total_pages}"
        x_position = self.width - 32  # margen derecho
        y_position = 20  # distancia desde el borde inferior
        self.c.drawRightString(x_position, y_position, footer_text)

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

        lines = self._wrap_text(text, font_name, font_size, max_width)

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
        background_color = kwargs.get('background_color')
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
                Paragraph(str(cell or ''), style_paragraph) for cell in row]
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

        for row_idx in background_rows:
            style.add('BACKGROUND', (0, row_idx),
                      (-1, row_idx), background_color)

        for col_idx in background_cols:
            style.add('BACKGROUND', (col_idx, 0),
                      (col_idx, len(data) - 1), background_color)

        if show_grid:
            style.add('GRID', (0, 0), (-1, -1), 0.5, colors.black)

        table.setStyle(style)
        table.wrapOn(self.c, 0, 0)
        table.drawOn(self.c, coord_x, y - row_height * len(data))

    def add_materials_table(self, coord_x, data, col_widths=None, **kwargs):
        font_name = kwargs.get('font_name', 'Arial')
        font_size = kwargs.get('font_size', 8)

        headers = [
            "Clave del Producto", "Color", "Cantidad", "Descripción",
            "Unidad", "P. Unitario", "Total"
        ]
        all_rows = [headers] + data

        # Estilos por columna
        paragraph_styles = []
        for i in range(len(headers)):
            alignment = 'CENTER' if i < 5 else 'RIGHT'
            paragraph_styles.append(ParagraphStyle(
                name=f"Col{i}",
                fontName=font_name,
                fontSize=font_size,
                leading=font_size + 2,
                alignment={'LEFT': 0, 'CENTER': 1, 'RIGHT': 2}[alignment]
            ))

        # Envolver contenido como Paragraphs
        wrapped_data = []
        for row in all_rows:
            wrapped_row = []
            for col_idx, cell in enumerate(row):
                value = str(cell or '')
                if row != headers and col_idx in [5, 6]:  # formato monetario
                    try:
                        number = float(str(cell).replace(
                            '$', '').replace(',', ''))
                        value = f"${number:,.2f}"
                    except (ValueError, TypeError):
                        pass
                wrapped_row.append(Paragraph(value, paragraph_styles[col_idx]))
            wrapped_data.append(wrapped_row)

        # Estilo tabla
        table_style = TableStyle()
        table_style.add('FONT', (0, 0), (-1, -1), font_name, font_size)
        table_style.add('GRID', (0, 0), (-1, -1), 0.5, colors.black)
        table_style.add('VALIGN', (0, 0), (-1, -1), 'MIDDLE')
        table_style.add('LEFTPADDING', (0, 0), (-1, -1), 2)
        table_style.add('RIGHTPADDING', (0, 0), (-1, -1), 2)
        table_style.add('ALIGN', (0, 0), (4, -1), 'CENTER')
        table_style.add('ALIGN', (5, 0), (6, -1), 'RIGHT')
        table_style.add('BACKGROUND', (0, 0), (-1, 0), colors.darkgrey)
        table_style.add('TEXTCOLOR', (0, 0), (-1, 0), colors.white)
        table_style.add('BACKGROUND', (6, 1),
                        (6, len(wrapped_data) - 1), colors.lightgrey)

        row_height = kwargs.get("row_height", 18)

        first_page_margin_top = 235
        other_pages_margin_top = 30
        margin_bottom = 40

        max_rows_first_page = 20
        max_rows_other_pages = int(
            (self.page_height - other_pages_margin_top - margin_bottom) // row_height)

        row_count = 0
        page_index = 0
        pages_data = []
        current_page_rows = [wrapped_data[0]]  # encabezado

        for row in wrapped_data[1:]:
            max_rows = max_rows_first_page if page_index == 0 else max_rows_other_pages
            if row_count >= max_rows:
                pages_data.append(current_page_rows)
                current_page_rows = [wrapped_data[0], row]
                row_count = 1
                page_index += 1
            else:
                current_page_rows.append(row)
                row_count += 1
        if current_page_rows:
            pages_data.append(current_page_rows)

        # Poner el cursor para la primera página sólo una vez antes del ciclo
        self.y_cursor = self.page_height - first_page_margin_top
        total_pages = len(pages_data)
        for i, table_rows in enumerate(pages_data):
            if i > 0:
                self._add_page(margin_top=other_pages_margin_top)
                self.c.setFont(font_name, font_size)
            # Para la página 0 no llamar _add_page, ya que es la página inicial

            table = Table(table_rows, colWidths=col_widths)
            table.setStyle(table_style)

            available_width = sum(
                col_widths) if col_widths else self.width - 2 * coord_x
            _, table_height = table.wrap(available_width, self.y_cursor)
            table.drawOn(self.c, coord_x, self.y_cursor - table_height)

            self.y_cursor -= table_height + 10

            self._add_footer(i + 1, total_pages)

        # NO incrementar current_page_index aquí porque _add_page ya lo hace
        self.is_new_page = False

        return self.current_page_index, self.y_cursor

    def add_qr_code(self, coord_x, coord_y, data, size=100):
        qr_code = qr.QrCodeWidget(data)
        bounds = qr_code.getBounds()
        width = bounds[2] - bounds[0]
        height = bounds[3] - bounds[1]

        d = Drawing(size, size, transform=[
                    size / width, 0, 0, size / height, 0, 0])
        d.add(qr_code)

        y = self.height - coord_y
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

    def merge(self):
        if not self.is_new_page:
            self.c.showPage()

        self.c.save()
        self.buffer.seek(0)

        template = PdfReader(self.template)
        overlay = PdfReader(self.buffer)
        writer = PdfWriter()

        # Mezclar la primera página del template con la primera página del overlay
        page = template.pages[0]
        page.merge_page(overlay.pages[0])
        writer.add_page(page)

        # Añadir las páginas restantes del overlay (buffer) sin template
        for i in range(1, len(overlay.pages)):
            writer.add_page(overlay.pages[i])

        with open(self.output_path, "wb") as f:
            writer.write(f)

    def generate(self):
        if not self.is_new_page:
            self.c.showPage()

        self.c.save()
        with open(self.output_path, "wb") as f:
            f.write(self.buffer.getvalue())
