import logging
from pathlib import Path

from django.conf import settings

from api.functions.pdf_generator import PDFGenerator
from api.helpers.formats import clean_text


def generate_pdf(data):
    try:
        supplier = data.get("supplier", {})
        supplier_name = supplier.get("name", "")

        # 📁 Rutas seguras
        base_dir = Path(settings.MEDIA_ROOT)
        template_path = base_dir / "templates" / "purchaseorder_template.pdf"

        output_dir = base_dir / "purchase_orders" / "pdf"
        output_dir.mkdir(parents=True, exist_ok=True)

        output_path = output_dir / (
            f"OC_{clean_text(data.get('client', 'cliente'))}_"
            f"{data.get('number', '')}_"
            f"{clean_text(supplier_name)}.pdf"
        )

        # 🧾 Inicializar generador
        pdf_generator = PDFGenerator(
            template=str(template_path),
            output_path=str(output_path),
            number=data.get("number"),
        )

        # 🧠 CONTENIDO PDF
        pdf_generator.add_wrap_text(30, 70, 220, data.get("company", ""))
        pdf_generator.add_wrap_text(250, 71, 220, [data.get("date", "")])

        pdf_generator.add_wrap_text(
            250, 96, 220, [data.get("number", "")], font_color="white"
        )
        pdf_generator.add_wrap_text(
            250, 122, 220, [data.get("location", "")], font_color="white"
        )

        pdf_generator.add_wrap_text(250, 155, 220, [data.get("division", "")])

        # 📦 Supplier
        supplier_data = [["NOMBRE:", supplier_name.upper()]]
        supplier_fields = [
            ("rfc", "RFC:"),
            ("address", "DIRECCIÓN:"),
            ("zipcode", "CP:"),
            ("email", "EMAIL:"),
            ("phone", "TELÉFONO:"),
        ]

        for key, label in supplier_fields:
            if supplier.get(key):
                supplier_data.append([label, supplier[key].upper()])

        pdf_generator.add_table(29, 162, supplier_data, [50, 170], font_size=7)

        # 🧱 Materiales
        _, remaining_y = pdf_generator.add_materials_table(
            29,
            data.get("materials", []),
            [70, 74, 70, 45, 130, 45, 60, 60],
            font_size=7.5,
        )

        remaining_y = pdf_generator.ensure_space(remaining_y, 35)

        # 📝 Observaciones
        pdf_generator.add_wrap_text(
            101, remaining_y, 300, ["OBSERVACIONES:"], font_color="gray"
        )
        pdf_generator.add_wrap_text(
            103,
            remaining_y + 10,
            312,
            [data.get("notes", "")],
            leading=12,
        )

        # 💰 Totales
        pdf_generator.add_table(
            463,
            remaining_y,
            [["Subtotal:"], ["(-) % Descuento"], ["(+) IVA 16%:"]],
            [59],
            font_size=7.5,
            background_color="#f5f5f5",
            background_cols=[0],
        )

        pdf_generator.add_table(
            522,
            remaining_y,
            data.get("subtotal", []),
            [59],
            font_size=7.5,
            show_grid=True,
            align="RIGHT",
        )

        pdf_generator.add_line(
            101, remaining_y, 314, 12, lines=3, line_color="gray", line_border=0.5
        )
        pdf_generator.add_line(
            101, remaining_y, 314, 12, lines=3, line_color="gray", line_border=0.5
        )

        pdf_generator.add_wrap_text(
            101,
            remaining_y + 50,
            314,
            ["Este documento NO ES UNA FACTURA."],
            font_name="Arial Italic",
            font_color="gray",
        )

        pdf_generator.add_table(
            463,
            remaining_y + 40,
            [["TOTAL"]],
            [59],
            font_size=7.5,
            background_color="gray",
            background_cols=[0],
            show_grid=True,
            font_name="Arial Italic",
            align="CENTER",
            text_color="white",
        )

        remaining_y = pdf_generator.add_table(
            522,
            remaining_y + 40,
            [[data.get("total", "")]],
            [59],
            font_size=7.5,
            show_grid=True,
            align="RIGHT",
            font_name="Arial Italic",
        )

        remaining_y = pdf_generator.ensure_space(remaining_y, 30)

        # 🔗 Línea + QR
        pdf_generator.add_line(29, remaining_y, 554, 12, line_border=0.5)

        pdf_generator.add_qr_code(
            490,
            remaining_y + 8,
            f"{settings.ADMIN_URL}apps/purchase-orders/view/{data.get('purchase_order_id')}?input=true",
            70,
        )

        # 🧾 Facturación
        billing_table = [
            ["FACTURACIÓN:",
                f"MÉTODO DE PAGO: {data.get('payment_method', '')}"],
            ["", f"FORMA DE PAGO: {data.get('payment_form', '')}"],
            ["", f"USO DE CFDI: {data.get('cfdi', '')}"],
            ["", f"ENVIAR FACTURA A: {data.get('invoice_email', '')}"],
        ]

        remaining_y = pdf_generator.add_table(
            29, remaining_y + 25, billing_table, [164, 220], font_size=7.5
        )

        remaining_y = pdf_generator.ensure_space(remaining_y, 40)

        # ✍️ Firmas
        pdf_generator.add_line(29, remaining_y, 554, 12, line_border=0.5)

        pdf_generator.add_wrap_text(
            29, remaining_y + 25, 164, ["AUTORIZADO POR:"], font_size=7.5
        )

        pdf_generator.add_line(29, remaining_y + 45, 160, 12, line_border=0.5)
        pdf_generator.add_line(226, remaining_y + 45, 160, 12, line_border=0.5)
        pdf_generator.add_line(423, remaining_y + 45, 160, 12, line_border=0.5)

        pdf_generator.add_table(
            29,
            remaining_y + 60,
            [["DIRECCIÓN", "ARQ. EUGENIA REYNOSO", "DPTO. COMPRAS"]],
            [160, 234, 160],
            font_size=7.5,
            align="CENTER",
        )

        # 🧩 Generar PDF
        pdf_generator.merge()

        relative_path = output_path.relative_to(settings.MEDIA_ROOT)
        return str(relative_path)

    except Exception as e:
        logging.error(f"Error generando PDF: {e}")
        raise
