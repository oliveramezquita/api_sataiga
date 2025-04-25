from rest_framework import views
from api.use_cases.material_use_case import MaterialUseCase
from api.middlewares import BellartiAuthenticationMiddleware


class MatrialView(views.APIView):
    authentication_classes = [BellartiAuthenticationMiddleware]

    def post(self, request):
        use_case = MaterialUseCase(data=request.data)
        return use_case.save()

    def get(self, request):
        use_case = MaterialUseCase(request=request)
        return use_case.get()

    def put(self, request):
        use_case = MaterialUseCase(data=request.data)
        return use_case.upload()


class MaterialByIdView(views.APIView):
    authentication_classes = [BellartiAuthenticationMiddleware]

    def get(self, request, id):
        use_case = MaterialUseCase(id=id)
        return use_case.get_by_id()

    def patch(self, request, id):
        use_case = MaterialUseCase(data=request.data, id=id)
        return use_case.update()

    def delete(self, request, id):
        use_case = MaterialUseCase(id=id)
        return use_case.delete()
