"""
Emisión y validación de JWT para la app móvil de postventa.

El proyecto no usa `djangorestframework-simplejwt`; el patrón existente
(`api_sataiga/functions.py`) firma con PyJWT + `settings.AUTH_SECRET` (HS256).
Aquí se replica ese patrón añadiendo tipo de token, expiración y `jti`
para poder revocar refresh tokens (blacklist).
"""
import uuid
from datetime import timedelta

import jwt
from django.conf import settings

from .errors import AuthError
from .timeutils import utcnow

ALGORITHM = "HS256"

TOKEN_ACCESS = "access"
TOKEN_REFRESH = "refresh"
TOKEN_ACTIVATION = "activation"
TOKEN_PASSWORD_RESET = "password_reset"


def _access_ttl():
    return getattr(settings, "AUTH_ACCESS_TOKEN_LIFETIME", timedelta(minutes=30))


def _refresh_ttl():
    return getattr(settings, "AUTH_REFRESH_TOKEN_LIFETIME", timedelta(days=30))


def _onboarding_ttl():
    return getattr(settings, "AUTH_ONBOARDING_TOKEN_LIFETIME", timedelta(minutes=15))


def _encode(payload):
    token = jwt.encode(payload, settings.AUTH_SECRET, algorithm=ALGORITHM)
    # PyJWT < 2 devolvía bytes; normalizamos.
    return token.decode("utf-8") if isinstance(token, bytes) else token


def _base_claims(auth):
    return {
        "sub": str(auth["_id"]),
        "user_id": str(auth["user_id"]) if auth.get("user_id") else None,
        "user_type": auth.get("user_type"),
    }


def issue_token_pair(auth):
    now = utcnow()
    access_exp = now + _access_ttl()
    base = _base_claims(auth)

    access = _encode({
        **base,
        "type": TOKEN_ACCESS,
        "iat": now,
        "exp": access_exp,
    })
    refresh = _encode({
        **base,
        "type": TOKEN_REFRESH,
        "jti": uuid.uuid4().hex,
        "iat": now,
        "exp": now + _refresh_ttl(),
    })
    return {
        "access": access,
        "refresh": refresh,
        "token_type": "Bearer",
        "expires_in": int(_access_ttl().total_seconds()),
    }


def issue_onboarding_token(auth, purpose):
    """Token corto que acredita haber pasado el 2FA (activación / reset)."""
    now = utcnow()
    return _encode({
        **_base_claims(auth),
        "type": purpose,
        "iat": now,
        "exp": now + _onboarding_ttl(),
    })


def decode_token(token, expected_type=None):
    try:
        payload = jwt.decode(token, settings.AUTH_SECRET, algorithms=[ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise AuthError(
            "El token expiró.", code="token_expired", status_code=401
        )
    except jwt.InvalidTokenError:
        raise AuthError(
            "Token no válido.", code="token_invalid", status_code=401
        )

    if expected_type and payload.get("type") != expected_type:
        raise AuthError(
            "Token no válido para esta operación.",
            code="token_invalid",
            status_code=401,
        )
    return payload
