from django.conf import settings
from api.constants import EMAIL_NOTIFICATIONS
from api.helpers.formats import to_money
from api.tasks.email_tasks import send_email_notification


def notify_email(event_type: str, data: dict):
    config = EMAIL_NOTIFICATIONS.get(event_type)

    if not config:
        return

    template = f"mail_templated/{config['template']}"
    to, cc, bcc = config['recipients']

    if event_type == "purchase_order_created":
        context = {
            'subject': f"Nueva orden de compra: {data.get('project', '')} - {data.get('number', '')}",
            'link_href': f"{settings.ADMIN_URL}apps/purchase-orders/view/{data.get('id')}",
            'link_label': 'VER ORDEN DE COMPRA',
            'number': data.get('number'),
            'created': data.get('created'),
            'estimated_delivery': data.get('estimated_delivery'),
            'project': data.get('project'),
            'payment_method': data.get('payment_method'),
            'payment_form': data.get('payment_form'),
            'cfdi': data.get('cfdi'),
            'invoice_email': data.get('invoice_email'),
            'subtotal': to_money(data.get('subtotal', 0)),
            'iva': to_money(data.get('iva', 0)),
            'total': to_money(data.get('total', 0)),
            'comments': data.get('subject')
        }

    elif event_type == "invoice_uploaded":
        context = {
            'subject': f"Factura subida - {data.get('folio', '')}",
            'link_href': f"{settings.ADMIN_URL}apps/invoices/view/{str(data.get('_id'))}",
            'link_label': 'VER ORDEN DE COMPRA',
            'folio': data.get('folio', ''),
            'purchase_order': data.get('purchase_order', ''),
            'status': 'Pagada' if data.get('status') == 1 else 'Pendiente'
        }

    else:
        return

    if to:
        send_email_notification.delay(template, context, to, cc, bcc)
