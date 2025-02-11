from rest_framework import exceptions
from sataiga_api.functions import decode_user
from rest_framework import authentication
from api.models.user import User
import logging

log = logging.getLogger(__name__)


class InvalidAccessTokenError(Exception):
    pass


class SataigaAuthenticationMiddleware(authentication.BaseAuthentication):
    def authenticate(self, request):
        token = request.headers.get("authorization", None)
        try:
            if not token:
                raise exceptions.AuthenticationFailed(
                    'Token de acceso no válido.')

            token = token.split(" ")[1]
            user = self.get_user_from_token(token)
            return (user, None)

        except InvalidAccessTokenError as e:
            raise exceptions.NotFound(
                "No puedo obtener información con el token actual.")

    def get_user_from_token(self, token: str):
        payload = decode_user(token)
        user = User.objects.filter(id=payload['id']).first()
        if user is None:
            raise InvalidAccessTokenError
        return user
