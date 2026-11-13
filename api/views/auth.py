
import jwt

from bson import ObjectId
from django.conf import settings
from django.http import JsonResponse

from rest_framework import views
from rest_framework.permissions import AllowAny

from api.use_cases.auth_use_case import AuthUseCase
from api.services.refresh_token_service import RefreshTokenService
from api_sataiga.functions import (
    encode_user,
    decode_refresh_token,
)
from api_sataiga.handlers.mongodb_handler import MongoDBHandler


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
        # Validar el origen de la petición.
        # Esta vista utiliza una cookie como credencial.
        origin = request.headers.get("Origin")

        allowed_origins = set(settings.CORS_ALLOWED_ORIGINS)

        if settings.DEBUG:
            allowed_origins.update({
                "http://localhost:5173",
                "http://127.0.0.1:5173",
            })

        if origin not in allowed_origins:
            return JsonResponse(
                {"error": "Origen no autorizado"},
                status=403,
            )

        # Obtener Refresh Token desde la cookie
        refresh_token = request.COOKIES.get(
            "bellarti_refresh"
        )

        if not refresh_token:
            return JsonResponse(
                {"error": "Refresh Token no encontrado"},
                status=401,
            )

        try:
            # Validar firma, tipo y expiración
            payload = decode_refresh_token(refresh_token)

            user_id = payload["sub"]

            # Validar identificador de MongoDB
            if not ObjectId.is_valid(user_id):
                return JsonResponse(
                    {"error": "Token inválido"},
                    status=401,
                )

            # Comprobar que el usuario siga activo
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

            # Rotar el token anterior en Redis
            new_refresh_token = RefreshTokenService.refresh(
                refresh_token
            )

            if not new_refresh_token:
                return JsonResponse(
                    {"error": "Refresh Token revocado o utilizado"},
                    status=401,
                )

            # Generar Access Token con el mismo formato
            # que el login actual de Bellarti
            from api.serializers.user_serializer import UserSerializer

            user = UserSerializer(users[0]).data
            user.pop("permissions", None)

            access_token = encode_user(user)

            response = JsonResponse({
                "accessToken": access_token,
                "expiresIn": 28800,
            })

            # Actualizar cookie HttpOnly
            response.set_cookie(
                key="bellarti_refresh",
                value=new_refresh_token,
                max_age=7 * 24 * 60 * 60,
                httponly=True,
                secure=not settings.DEBUG,
                samesite="Lax",
                path="/api/",
            )

            return response

        except jwt.InvalidTokenError:
            return JsonResponse(
                {"error": "Refresh Token inválido o expirado"},
                status=401,
            )
