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

    def patch(self, request, id):
        use_case = InboundUseCase(data=request.data, id=id)
        return use_case.update()

    def delete(self, request, id):
        use_case = InboundUseCase(id=id)
        return use_case.delete()


class ProjectsListView(views.APIView):
    authentication_classes = [BellartiAuthenticationMiddleware]

    def get(self, request, project_type):
        use_case = InboundUseCase(request=request, project_type=project_type)
        return use_case.get_project()


class InboundsByMaterialView(views.APIView):
    authentication_classes = [BellartiAuthenticationMiddleware]

    def get(self, request, material):
        use_case = InboundUseCase(request=request, material=material)
        return use_case.get_by_material()
