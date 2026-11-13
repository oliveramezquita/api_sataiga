
import jwt  # type: ignore
import json
import uuid

from datetime import datetime, timedelta, timezone
from mail_templated import send_mail
from django.conf import settings
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from api_sataiga.handlers.mongodb_handler import MongoDBHandler
from api.serializers.notification_serializer import NotificationSerializer


def encode_user(user):
    """
    Genera un Access Token válido durante 8 horas.
    """
    now = datetime.now(timezone.utc)

    payload = {
        **user,
        "token_type": "access",
        "iat": now,
        "exp": now + timedelta(hours=8),
    }

    return jwt.encode(
        payload=payload,
        key=settings.AUTH_SECRET,
        algorithm="HS256"
    )


def decode_user(token):
    """
    Valida los Access Tokens nuevos y antiguos.

    - Los tokens nuevos deben tener tipo 'access'
      y fecha de expiración.
    - Los tokens antiguos se aceptan temporalmente.
    - Los Refresh Tokens se rechazan.
    """
    payload = jwt.decode(
        jwt=token,
        key=settings.AUTH_SECRET,
        algorithms=["HS256"]
    )

    token_type = payload.get("token_type")

    if token_type == "refresh":
        raise jwt.InvalidTokenError(
            "No se puede usar un Refresh Token como Access Token"
        )

    if token_type == "access":
        if "exp" not in payload:
            raise jwt.InvalidTokenError(
                "El Access Token no contiene expiración"
            )

    elif token_type is None:
        # Compatibilidad temporal con tokens anteriores.
        # Solo se acepta el formato antiguo que contiene _id.
        if not payload.get("_id"):
            raise jwt.InvalidTokenError(
                "Token antiguo inválido"
            )

        # Evitar aceptar tokens de otro formato.
        if any(
            key in payload for key in ("sub", "jti", "iss")
        ):
            raise jwt.InvalidTokenError(
                "Formato de token no permitido"
            )

    else:
        raise jwt.InvalidTokenError(
            "Tipo de token no permitido"
        )

    return payload


def encode_refresh_token(user):
    """
    Genera un Refresh Token válido durante 7 días.
    """
    now = datetime.now(timezone.utc)

    payload = {
        "sub": str(user["_id"]),
        "token_type": "refresh",
        "jti": str(uuid.uuid4()),
        "iat": now,
        "exp": now + timedelta(days=7),
    }

    return jwt.encode(
        payload=payload,
        key=settings.AUTH_SECRET,
        algorithm="HS256"
    )


def decode_refresh_token(token):
    """
    Valida la firma, expiración y tipo
    del Refresh Token.
    """
    payload = jwt.decode(
        jwt=token,
        key=settings.AUTH_SECRET,
        algorithms=["HS256"],
        options={
            "require": [
                "sub",
                "token_type",
                "jti",
                "iat",
                "exp",
            ]
        },
    )

    if payload["token_type"] != "refresh":
        raise jwt.InvalidTokenError(
            "El token no es un Refresh Token"
        )

    return payload


def hex_encode(data):
    json_data = json.dumps(data)
    json_bytes = json_data.encode('utf-8')
    return json_bytes.hex()


def hex_decode(data):
    decoded_bytes = bytes.fromhex(data)
    decoded_json_data = decoded_bytes.decode('utf-8')
    return json.loads(decoded_json_data)


def send_email(template, context, to=None, cc=None, bcc=None):
    to = to or []
    cc = cc or []
    bcc = bcc or []
    send_mail(
        template_name=template,
        context=context,
        from_email='Sistema Bellarti <info@bellarti.com.mx>',
        recipient_list=to,
        cc=cc,
        bcc=bcc
    )


def insert_notification(message):
    with MongoDBHandler('notifications') as db:
        notification_id = db.insert({**message})
        notification = db.extract({'_id': notification_id})
    return NotificationSerializer(notification[0]).data


def send_notification(message):
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        "notifications",
        {
            "type": "send_notification",
            "message": insert_notification(message)
        }
    )
