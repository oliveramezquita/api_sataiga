"""
Vistas de autenticación de la app móvil de postventa.

Son vistas delgadas: delegan toda la lógica en `AuthUseCase`, que devuelve
directamente un `JsonResponse` (mismo patrón que `api/views/auth.py`).
Todos los endpoints son públicos (la identidad se resuelve por credenciales
o por token en el cuerpo), por eso se desactiva la autenticación de DRF.
"""
from rest_framework import views
from rest_framework.permissions import AllowAny

from after_sales.use_cases.auth_use_case import AuthUseCase


class _PublicAuthView(views.APIView):
    authentication_classes = []
    permission_classes = [AllowAny]


class IdentifyView(_PublicAuthView):
    def post(self, request):
        return AuthUseCase(data=request.data).identify()


class VerificationSendView(_PublicAuthView):
    def post(self, request):
        return AuthUseCase(data=request.data).verification_send()


class VerificationConfirmView(_PublicAuthView):
    def post(self, request):
        return AuthUseCase(data=request.data).verification_confirm()


class ActivateView(_PublicAuthView):
    def post(self, request):
        return AuthUseCase(data=request.data).activate()


class LoginView(_PublicAuthView):
    def post(self, request):
        return AuthUseCase(data=request.data).login()


class TokenRefreshView(_PublicAuthView):
    def post(self, request):
        return AuthUseCase(data=request.data).token_refresh()


class LogoutView(_PublicAuthView):
    def post(self, request):
        return AuthUseCase(data=request.data).logout()


class PasswordResetRequestView(_PublicAuthView):
    def post(self, request):
        return AuthUseCase(data=request.data).password_reset_request()


class PasswordResetConfirmView(_PublicAuthView):
    def post(self, request):
        return AuthUseCase(data=request.data).password_reset_confirm()
