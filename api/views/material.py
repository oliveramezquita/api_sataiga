from rest_framework import views
from api.use_cases.material_use_case import MaterialUseCase
from api.middlewares import BellartiAuthenticationMiddleware


class MaterialsView(views.APIView):
    authentication_classes = [BellartiAuthenticationMiddleware]

    def post(self, request):
        use_case = MaterialUseCase(data=request.data)
        return use_case.save()

    def get(self, request):
        use_case = MaterialUseCase(request=request)
        return use_case.get()

    def put(self, request):
        use_case = MaterialUseCase(request=request, data=request.data)
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


class DownloadMaterialsView(views.APIView):
    authentication_classes = [BellartiAuthenticationMiddleware]

    def get(self, request):
        use_case = MaterialUseCase(request=request)
        return use_case.download()


class ImagesMaterialView(views.APIView):
    authentication_classes = [BellartiAuthenticationMiddleware]

    def patch(self, request, id):
        use_case = MaterialUseCase(request=request, id=id)
        return use_case.upload_image()

    def delete(self, request, id):
        use_case = MaterialUseCase(data=request.data, id=id)
        return use_case.delete_image()
