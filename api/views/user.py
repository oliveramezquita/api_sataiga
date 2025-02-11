from rest_framework import views
from api.use_cases.role_use_case import RoleUseCase
from api.use_cases.user_use_case import UserUseCase
from api.middlewares import SataigaAuthenticationMiddleware


class RolesView(views.APIView):
    authentication_classes = [SataigaAuthenticationMiddleware]

    def post(self, request):
        use_case = RoleUseCase(data=request.data)
        return use_case.save()

    def get(self, request):
        use_case = RoleUseCase()
        return use_case.get()


class RoleByIdView(views.APIView):
    def patch(self, request, id):
        use_case = RoleUseCase(data=request.data, id=id)
        return use_case.update()


class UsersView(views.APIView):
    authentication_classes = [SataigaAuthenticationMiddleware]

    def post(self, request):
        use_case = UserUseCase(data=request.data)
        return use_case.save()

    def get(self, request):
        use_case = UserUseCase(request=request)
        return use_case.get()


class UserByIdView(views.APIView):
    authentication_classes = [SataigaAuthenticationMiddleware]

    def post(self, request, id):
        use_case = UserUseCase(data=request.data, id=id)
        return use_case.register()

    def get(self, request, id):
        use_case = UserUseCase(id=id)
        return use_case.get_by_id()

    def patch(self, request, id):
        use_case = UserUseCase(data=request.data, id=id)
        return use_case.update()

    def delete(self, request, id):
        use_case = UserUseCase(id=id)
        return use_case.delete()


class UpdatePasswordView(views.APIView):
    authentication_classes = [SataigaAuthenticationMiddleware]

    def post(self, request, id):
        use_case = UserUseCase(data=request.data, id=id)
        return use_case.update_password()
