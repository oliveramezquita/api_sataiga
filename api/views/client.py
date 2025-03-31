from rest_framework import views
from api.use_cases.client_use_case import ClientUseCase
from api.middlewares import BellartiAuthenticationMiddleware


class ClientView(views.APIView):
    authentication_classes = [BellartiAuthenticationMiddleware]

    def post(self, request):
        use_case = ClientUseCase(data=request.data)
        return use_case.save()


class ClientByTypeView(views.APIView):
    authentication_classes = [BellartiAuthenticationMiddleware]

    def get(self, request, client_type):
        use_case = ClientUseCase(request=request, client_type=client_type)
        return use_case.get()


class ClientByIdView(views.APIView):
    authentication_classes = [BellartiAuthenticationMiddleware]

    def get(self, request, id):
        use_case = ClientUseCase(id=id)
        return use_case.get_by_id()

    def patch(self, request, id):
        use_case = ClientUseCase(data=request.data, id=id)
        return use_case.update()

    def delete(self, request, id):
        use_case = ClientUseCase(id=id)
        return use_case.delete()
