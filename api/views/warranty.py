from rest_framework import views
from api.use_cases.warranty_use_case import WarrantyUseCase
from api.middlewares import BellartiAuthenticationMiddleware


class WarrantiesView(views.APIView):
    authentication_classes = [BellartiAuthenticationMiddleware]

    def post(self, request):
        use_case = WarrantyUseCase(data=request.data)
        return use_case.save()

    def get(self, request):
        use_case = WarrantyUseCase(request=request)
        return use_case.get()


class WarrantyView(views.APIView):
    authentication_classes = [BellartiAuthenticationMiddleware]

    def get(self, request, id):
        use_case = WarrantyUseCase(id=id)
        return use_case.get_by_id()

    def patch(self, request, id):
        use_case = WarrantyUseCase(data=request.data, id=id)
        return use_case.update()


class WarrantyAvailabilityView(views.APIView):
    authentication_classes = [BellartiAuthenticationMiddleware]

    def patch(self, request, action, id):
        use_case = WarrantyUseCase(action=action, id=id)
        return use_case.availability()
