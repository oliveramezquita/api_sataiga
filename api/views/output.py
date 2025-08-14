from rest_framework import views
from api.use_cases.output_use_case import OutputUseCase
from api.middlewares import BellartiAuthenticationMiddleware


class OutputsView(views.APIView):
    authentication_classes = [BellartiAuthenticationMiddleware]

    def get(self, request):
        use_case = OutputUseCase(request=request)
        return use_case.get()

    def post(self, request):
        use_case = OutputUseCase(data=request.data)
        return use_case.save()


class OutputView(views.APIView):
    authentication_classes = [BellartiAuthenticationMiddleware]

    def get(self, request, id):
        use_case = OutputUseCase(id=id)
        return use_case.get_by_id()

    def patch(self, request, id):
        use_case = OutputUseCase(id=id, data=request.data)
        return use_case.update()


class OutputsByMaterialView(views.APIView):
    authentication_classes = [BellartiAuthenticationMiddleware]

    def get(self, request, material):
        use_case = OutputUseCase(request=request, material=material)
        return use_case.get_by_material()
