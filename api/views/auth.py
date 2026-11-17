import logging
import jwt

from bson import ObjectId
from django.conf import settings
from django.http import JsonResponse

from rest_framework import views
from rest_framework.permissions import AllowAny

from api.use_cases.auth_use_case import AuthUseCase
from api.services.refresh_token_service import RefreshTokenService
from api.serializers.user_serializer import UserSerializer

from api_sataiga.functions import (
    encode_user,
    decode_refresh_token,
)
from api_sataiga.handlers.mongodb_handler import MongoDBHandler


logger = logging.getLogger(__name__)

REFRESH_COOKIE_NAME = "bellarti_refresh"
REFRESH_COOKIE_PATH = "/api/"


def is_allowed_origin(request):
    """
    Verifica el origen para operaciones
    autenticadas mediante cookies.
    """
    origin = request.headers.get("Origin")

    allowed_origins = set(settings.CORS_ALLOWED_ORIGINS)

    if settings.DEBUG:
        allowed_origins.update({
            "http://localhost:5173",
            "http://127.0.0.1:5173",
        })

    return origin in allowed_origins


class AuthView(views.APIView):

    def post(self, request):
        use_case = AuthUseCase(data=request.data)
        return use_case.login()


class PasswordRequestView(views.APIView):

    def post(self, request):
        use_case = AuthUseCase(data=request.data)
        return use_case.password_request()


class RestorePasswordView(views.APIView):

    def post(self, request):
        use_case = AuthUseCase(data=request.data)
        return use_case.restore_password()


class RefreshTokenView(views.APIView):

    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        if not is_allowed_origin(request):
            return JsonResponse(
                {"error": "Origen no autorizado"},
                status=403,
            )

        refresh_token = request.COOKIES.get(
            REFRESH_COOKIE_NAME
        )

        if not refresh_token:
            return JsonResponse(
                {"error": "Refresh Token no encontrado"},
                status=401,
            )

        try:
            payload = decode_refresh_token(refresh_token)
            user_id = payload["sub"]

            if not ObjectId.is_valid(user_id):
                return JsonResponse(
                    {"error": "Token inválido"},
                    status=401,
                )

            with MongoDBHandler("users") as db:
                users = db.extract({
                    "_id": ObjectId(user_id),
                    "status": 1,
                })

            if not users:
                return JsonResponse(
                    {"error": "Usuario no encontrado o inactivo"},
                    status=401,
                )

            user = UserSerializer(users[0]).data
            user.pop("permissions", None)

            new_refresh_token = RefreshTokenService.refresh(
                refresh_token
            )

            if not new_refresh_token:
                return JsonResponse(
                    {"error": "Refresh Token revocado o utilizado"},
                    status=401,
                )

            response = JsonResponse({
                "accessToken": encode_user(user),
                "expiresIn": 28800,
            })

            response.set_cookie(
                key=REFRESH_COOKIE_NAME,
                value=new_refresh_token,
                max_age=7 * 24 * 60 * 60,
                httponly=True,
                secure=not settings.DEBUG,
                samesite="Lax",
                path=REFRESH_COOKIE_PATH,
            )

            return response

        except jwt.InvalidTokenError:
            return JsonResponse(
                {"error": "Refresh Token inválido o expirado"},
                status=401,
            )


class LogoutView(views.APIView):

    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        if not is_allowed_origin(request):
            return JsonResponse(
                {"error": "Origen no autorizado"},
                status=403,
            )

        refresh_token = request.COOKIES.get(
            REFRESH_COOKIE_NAME
        )

        if refresh_token:
            try:
                RefreshTokenService.revoke(refresh_token)

            except jwt.InvalidTokenError:
                # El token ya expiró o es inválido.
                # Permitimos limpiar la cookie.
                pass

            except Exception:
                logger.exception(
                    "No fue posible revocar el Refresh Token"
                )

                return JsonResponse(
                    {"error": "No fue posible cerrar la sesión"},
                    status=503,
                )

        response = JsonResponse({
            "message": "Sesión cerrada correctamente"
        })

        response.delete_cookie(
            key=REFRESH_COOKIE_NAME,
            path=REFRESH_COOKIE_PATH,
            samesite="Lax",
        )

        return response
