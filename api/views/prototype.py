from rest_framework import views
from api.use_cases.prototype_use_case import PrototypeUseCase
from api.middlewares import BellartiAuthenticationMiddleware


class PrototypeView(views.APIView):
    authentication_classes = [BellartiAuthenticationMiddleware]

    def post(self, request):
        use_case = PrototypeUseCase(data=request.data)
        return use_case.save()

    def get(self, request):
        use_case = PrototypeUseCase(request=request)
        return use_case.get()


class PrototypeByIdView(views.APIView):
    authentication_classes = [BellartiAuthenticationMiddleware]

    def get(self, request, id):
        use_case = PrototypeUseCase(id=id)
        return use_case.get_by_id()

    def patch(self, request, id):
        use_case = PrototypeUseCase(data=request.data, id=id)
        return use_case.update()

    def delete(self, request, id):
        use_case = PrototypeUseCase(id=id)
        return use_case.delete()
