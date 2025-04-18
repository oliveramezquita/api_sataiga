from rest_framework import views
from api.use_cases.role_use_case import RoleUseCase
from api.middlewares import BellartiAuthenticationMiddleware


class RoleView(views.APIView):
    authentication_classes = [BellartiAuthenticationMiddleware]

    def post(self, request):
        use_case = RoleUseCase(data=request.data)
        return use_case.save()

    def get(self, request):
        use_case = RoleUseCase(request=request)
        return use_case.get()


class RoleByIdView(views.APIView):
    authentication_classes = [BellartiAuthenticationMiddleware]

    def patch(self, request, id):
        use_case = RoleUseCase(data=request.data, id=id)
        return use_case.update()

    def get(self, request, id):
        use_case = RoleUseCase(id=id)
        return use_case.get_by_id()

    def delete(self, request, id):
        use_case = RoleUseCase(id=id)
        return use_case.delete()


class UpdatePermissionsView(views.APIView):
    authentication_classes = [BellartiAuthenticationMiddleware]

    def patch(self, request, id):
        use_case = RoleUseCase(data=request.data, id=id)
        return use_case.update_permissions()
