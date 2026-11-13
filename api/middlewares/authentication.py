
import jwt
from bson import ObjectId
from rest_framework import authentication, exceptions
from api_sataiga.functions import decode_user
from api_sataiga.handlers.mongodb_handler import MongoDBHandler


class BellartiAuthenticationMiddleware(authentication.BaseAuthentication):

    def authenticate_header(self, request):
        return "Bearer"

    def authenticate(self, request):
        authorization = request.headers.get(
            "Authorization", ""
        )

        parts = authorization.split()

        if len(parts) != 2 or parts[0].lower() != "bearer":
            raise exceptions.AuthenticationFailed(
                "Token de acceso no válido"
            )

        token = parts[1]

        try:
            payload = decode_user(token)

        except jwt.ExpiredSignatureError:
            raise exceptions.AuthenticationFailed(
                "El token de acceso ha expirado",
                code="token_expired"
            )

        except jwt.InvalidTokenError:
            raise exceptions.AuthenticationFailed(
                "Token de acceso no válido",
                code="invalid_token"
            )

        user_id = payload.get("_id")

        if not user_id:
            raise exceptions.AuthenticationFailed(
                "Token sin identificador de usuario"
            )

        with MongoDBHandler("users") as db:
            users = db.extract({
                "_id": ObjectId(user_id),
                "status": 1,
            })

        if not users:
            raise exceptions.AuthenticationFailed(
                "Usuario no encontrado o inactivo"
            )

        return (users[0], None)
