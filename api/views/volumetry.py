from rest_framework import views
from api.use_cases.volumetry_use_case import VolumetryUseCase
from api.middlewares import BellartiAuthenticationMiddleware


class VolumetryView(views.APIView):
    authentication_classes = [BellartiAuthenticationMiddleware]

    def post(self, request):
        use_case = VolumetryUseCase(data=request.data)
        return use_case.save()
