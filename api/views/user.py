from rest_framework import views
from api.use_cases.user_use_case import UserUseCase
from api.middlewares import BellartiAuthenticationMiddleware


class UserView(views.APIView):
    authentication_classes = [BellartiAuthenticationMiddleware]

    def post(self, request):
        use_case = UserUseCase(data=request.data)
        return use_case.save()

    def get(self, request):
        use_case = UserUseCase(request=request)
        return use_case.get()


class UserByIdView(views.APIView):
    authentication_classes = [BellartiAuthenticationMiddleware]

    def get(self, request, id):
        use_case = UserUseCase(id=id)
        return use_case.get_by_id()

    def patch(self, request, id):
        use_case = UserUseCase(data=request.data, id=id)
        return use_case.update()

    def delete(self, request, id):
        use_case = UserUseCase(id=id)
        return use_case.delete()


class RegisterView(views.APIView):
    def post(self, request, id):
        use_case = UserUseCase(data=request.data, id=id)
        return use_case.register()


class UpdatePasswordView(views.APIView):
    authentication_classes = [BellartiAuthenticationMiddleware]

    def patch(self, request, id):
        use_case = UserUseCase(data=request.data, id=id)
        return use_case.update_password()
