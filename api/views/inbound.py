from rest_framework import views
from api.use_cases.inbound_use_case import InboundUseCase
from api.middlewares import BellartiAuthenticationMiddleware


class InboundsView(views.APIView):
    authentication_classes = [BellartiAuthenticationMiddleware]

    def get(self, request):
        use_case = InboundUseCase(request=request)
        return use_case.get()

    def post(self, request):
        use_case = InboundUseCase(data=request.data)
        return use_case.save()


class InboundView(views.APIView):
    authentication_classes = [BellartiAuthenticationMiddleware]

    def get(self, request, id):
        use_case = InboundUseCase(id=id)
        return use_case.get_by_id()


class ProjectsListView(views.APIView):
    authentication_classes = [BellartiAuthenticationMiddleware]

    def get(self, request, project_type):
        use_case = InboundUseCase(request=request, project_type=project_type)
        return use_case.get_project()
