from rest_framework import views
from api.use_cases.section_use_case import SectionUseCase
from api.middlewares import BellartiAuthenticationMiddleware


class SectionView(views.APIView):
    authentication_classes = [BellartiAuthenticationMiddleware]

    def post(self, request):
        use_case = SectionUseCase(data=request.data)
        return use_case.save()

    def get(self, request):
        use_case = SectionUseCase(request=request)
        return use_case.get()


class SectionViewById(views.APIView):
    authentication_classes = [BellartiAuthenticationMiddleware]

    def patch(self, request, id):
        use_case = SectionUseCase(data=request.data, id=id)
        return use_case.update()
