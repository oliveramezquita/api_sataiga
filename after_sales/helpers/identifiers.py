import re

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
_PHONE_CLEAN_RE = re.compile(r"[\s\-().]")
_PHONE_RE = re.compile(r"^\+?\d{7,15}$")


def classify_identifier(value):
    """
    Determina si `value` es un correo o un teléfono y lo normaliza.

    Devuelve (kind, normalized) donde kind es 'email', 'phone' o None.
    - email  -> minúsculas, sin espacios
    - phone  -> sólo dígitos y un '+' opcional al inicio
    """
    value = (value or "").strip()
    if not value:
        return None, None

    if _EMAIL_RE.match(value):
        return "email", value.lower()

    phone = _PHONE_CLEAN_RE.sub("", value)
    if _PHONE_RE.match(phone):
        return "phone", phone

    return None, value


def mask_phone(phone):
    """'+5213331234567' -> '•••••••4567' (para pistas en la respuesta)."""
    if not phone:
        return None
    digits = _PHONE_CLEAN_RE.sub("", phone)
    tail = digits[-4:]
    return f"{'•' * max(len(digits) - 4, 0)}{tail}"
