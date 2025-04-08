from rest_framework import views
from api.use_cases.volumetry_use_case import VolumetryUseCase
from api.middlewares import BellartiAuthenticationMiddleware


class VolumetryView(views.APIView):
    authentication_classes = [BellartiAuthenticationMiddleware]

    def post(self, request):
        use_case = VolumetryUseCase(data=request.data)
        return use_case.save()

    def get(self, request):
        use_case = VolumetryUseCase(request=request)
        return use_case.get()


class VolumetryByIdView(views.APIView):
    authentication_classes = [BellartiAuthenticationMiddleware]

    def delete(self, request, id):
        use_case = VolumetryUseCase(id=id)
        return use_case.delete()


class VolumetryUploadView(views.APIView):
    authentication_classes = [BellartiAuthenticationMiddleware]

    def post(self, request):
        use_case = VolumetryUseCase(request=request, data=request.data)
        return use_case.upload()
