import hashlib
import hmac
import secrets

from django.conf import settings


def generate_code(length=None):
    length = length or getattr(settings, "AUTH_SMS_CODE_LENGTH", 6)
    return "".join(secrets.choice("0123456789") for _ in range(length))


def hash_code(code):
    """
    HMAC-SHA256 con SECRET_KEY. El modelo AuthVerification recomienda
    almacenar el hash del código y no el texto plano.
    """
    return hmac.new(
        settings.SECRET_KEY.encode("utf-8"),
        (code or "").encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


def verify_code(code, hashed):
    return hmac.compare_digest(hash_code(code), hashed or "")
