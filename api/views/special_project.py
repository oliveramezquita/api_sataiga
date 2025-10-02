from rest_framework import views
from api.use_cases.special_project_use_case import SpecialProjectUseCase
from api.middlewares import BellartiAuthenticationMiddleware


class SpecialProjectsView(views.APIView):
    authentication_classes = [BellartiAuthenticationMiddleware]

    def get(self, request, client_id):
        use_case = SpecialProjectUseCase(request=request, client_id=client_id)
        return use_case.get()


class ClientListView(views.APIView):
    authentication_classes = [BellartiAuthenticationMiddleware]

    def get(self, request):
        use_case = SpecialProjectUseCase(request=request)
        return use_case.get_clients()
