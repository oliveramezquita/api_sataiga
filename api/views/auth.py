from rest_framework import views
from api.use_cases.auth_use_case import AuthUseCase


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
