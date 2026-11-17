"""
Envío de SMS para la verificación en dos pasos.

TODO(product): el proyecto todavía no tiene un proveedor de SMS configurado
(no hay Twilio / Sinch / Vonage en requirements ni en settings). Por ahora el
backend por omisión sólo registra el mensaje en el log. Para producción:
implementar un backend real y apuntar `AFTER_SALES_SMS_BACKEND` a él.
"""
import logging

from django.conf import settings
from django.utils.module_loading import import_string

logger = logging.getLogger(__name__)

DEFAULT_BACKEND = "after_sales.services.sms.ConsoleSmsBackend"


class ConsoleSmsBackend:
    """Backend de desarrollo: no envía nada, sólo registra en el log."""

    def send(self, phone, message):
        logger.info("[SMS:console] to=%s | %s", phone, message)
        return True


def get_sms_backend():
    path = getattr(settings, "AFTER_SALES_SMS_BACKEND", DEFAULT_BACKEND)
    return import_string(path)()


def send_verification_sms(phone, code):
    message = (
        f"Tu código de verificación Bellarti es: {code}. "
        "No lo compartas con nadie."
    )
    return get_sms_backend().send(phone, message)
