import bcrypt
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError

from .errors import AuthError


def hash_password(raw):
    """Hash bcrypt, almacenado como str utf-8."""
    return bcrypt.hashpw(raw.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(raw, hashed):
    """Compara `raw` contra un hash bcrypt (str o bytes). None -> False."""
    if not hashed:
        return False
    if isinstance(hashed, str):
        hashed = hashed.encode("utf-8")
    try:
        return bcrypt.checkpw(raw.encode("utf-8"), hashed)
    except (ValueError, TypeError):
        return False


def validate_password_strength(raw):
    """Aplica los AUTH_PASSWORD_VALIDATORS del proyecto."""
    try:
        validate_password(raw)
    except DjangoValidationError as exc:
        raise AuthError(" ".join(exc.messages), code="weak_password")
