from rest_framework import exceptions
from api_sataiga.functions import decode_user
from rest_framework import authentication
from api_sataiga.handlers.mongodb_handler import MongoDBHandler


class InvalidAccessTokenError(Exception):
    pass


class BellartiAuthenticationMiddleware(authentication.BaseAuthentication):
    def authenticate(self, request):
        token = request.headers.get("authorization", None)
        try:
            if not token:
                raise exceptions.AuthenticationFailed(
                    'Token de acceso no válido')

            token = token.split(" ")[1]
            user = self.get_user_from_token(token)
            return (user, None)

        except InvalidAccessTokenError:
            raise exceptions.NotFound(
                "No puedo obtener información con el token actual")

    def get_user_from_token(self, token: str):
        payload = decode_user(token)
        with MongoDBHandler('user') as db:
            user = db.extract({'_id': payload['_id'], })

            if user is None:
                raise InvalidAccessTokenError

            return user
