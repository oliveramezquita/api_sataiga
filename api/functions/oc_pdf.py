import logging
from django.conf import settings
from api.functions.pdf_generator import PDFGenerator
from celery import shared_task
from api.helpers.format_str import clean_text


# def formato_moneda(valor, simbolo="$"):
#     try:
#         valor = float(valor)
#         return f"{simbolo} {valor:,.2f}"
#     except (ValueError, TypeError):
#         return f"{simbolo} 0.00"
log = logging.getLogger(__name__)


@shared_task
def generate_pdf(data):
    supplier_name = data['supplier']['name']
    pdf_generator = PDFGenerator(
        template='media/templates/purchaseorder_template.pdf',
        output_path=f'media/purchase_orders/pdf/OC_{clean_text(data['client'])}_{clean_text(data['purchase_order_id'])}_{clean_text(supplier_name)}.pdf',
        purchase_order_id=data['purchase_order_id'],
    )

    pdf_generator.add_wrap_text(30, 70, 220, data.get('company', []))
    pdf_generator.add_wrap_text(250, 71, 220, [data.get('date', '')])
    pdf_generator.add_wrap_text(
        250, 96, 220, [data['purchase_order_id']], font_color='white')
    pdf_generator.add_wrap_text(
        250, 122, 220, [data.get('location', '')], font_color='white')
    pdf_generator.add_wrap_text(250, 155, 220, [data.get('division', '')])
    supplier = data.get('supplier', {})
    supplier_data = [['NOMBRE:', supplier_name.upper()]]
    supplier_fields = [
        ('rfc', 'RFC:'),
        ('address', 'DIRECCIÓN:'),
        ('zipcode', 'CP:'),
        ('email', 'EMAIL:'),
        ('phone', 'TELÉFONO:')
    ]
    for key, label in supplier_fields:
        if key in supplier:
            supplier_data.append([label, supplier[key].upper()])
    pdf_generator.add_table(29, 130, supplier_data, [50, 170], font_size=7)
    pdf_generator.add_qr_code(
        485, 105, f"{settings.ADMIN_URL}purchase-orders/view/{data['purchase_order_id']}?input=true", 80)
    page_number, remaining_y = pdf_generator.add_materials_table(29, data.get(
        'materials', []), [70, 94, 50, 170, 50, 60, 60], font_size=7.5)
    log.info(f'page_number: {page_number}, remaining_y: {remaining_y}')
    pdf_generator.add_wrap_text(
        101, remaining_y, 300, ["OBSERVACIONES:"], font_color='gray')
    pdf_generator.add_table(463, remaining_y-18, [["Subtotal:"], ["(-) % Descuento"], ["(+) IVA 16%:"]], [
                            59], font_size=7.5, background_color='#f5f5f5', background_cols=[0])
    pdf_generator.add_table(522, remaining_y-18, data.get('subtotal', []),
                            [59], font_size=7.5, show_grid=True, align='RIGHT')
    pdf_generator.add_table(463, remaining_y+30, [["TOTAL"]], [59], font_size=7.5, background_color='gray', background_cols=[
                            0], show_grid=True, font_name='Arial Italic', align='CENTER', text_color='white')
    pdf_generator.add_table(522, remaining_y+30, [[data.get('total', '$ 0.00')]], [59],
                            font_size=7.5, show_grid=True, align='RIGHT', font_name='Arial Italic')
    pdf_generator.add_line(101, remaining_y, 314, 12, lines=3,
                           line_color='gray', line_border=0.5)
    pdf_generator.add_wrap_text(
        101, remaining_y+50, 314, ["Este documento NO ES UNA FACTURA."], font_name='Arial Italic', font_color='gray')
    pdf_generator.add_line(29, remaining_y+55, 554, 12, line_border=0.5)
    billing_table = [
        ["FACTURACIÓN:", "MÉTODO DE PAGO: POR DEFINIR"],
        ["", "FORMA DE PAGO: PPD (PAGO EN PARCIALIDADES)"],
        ["", "USO DE CFD: ADQUISICIÓN DE MERCANCÍAS"],
        ["", "ENVIAR FACTURA A: facturas@bellarti.com.mx"]
    ]
    pdf_generator.add_table(29, remaining_y+60, billing_table,
                            [164, 220], font_size=7.5)
    pdf_generator.add_line(29, remaining_y+115, 554, 12, line_border=0.5)
    pdf_generator.add_wrap_text(
        29, remaining_y+140, 164, ["AUTORIZADO POR:"], font_size=7.5)
    pdf_generator.add_line(29, remaining_y+174, 160, 12, line_border=0.5)
    pdf_generator.add_line(226, remaining_y+174, 160, 12, line_border=0.5)
    pdf_generator.add_line(423, remaining_y+174, 160, 12, line_border=0.5)
    pdf_generator.add_table(29, remaining_y+182, [["DIRECCIÓN", "ARQ. EUGENIA REYNOSO", "DPTO. COMPRAS"]], [
                            160, 234, 160], font_size=7.5, align='CENTER')
    pdf_generator.merge()
