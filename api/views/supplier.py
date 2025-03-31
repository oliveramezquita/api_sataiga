from rest_framework import views
from api.use_cases.supplier_use_case import SupplierUseCase
from api.middlewares import BellartiAuthenticationMiddleware


class SupplierView(views.APIView):
    authentication_classes = [BellartiAuthenticationMiddleware]

    def post(self, request):
        use_case = SupplierUseCase(data=request.data)
        return use_case.save()

    def get(self, request):
        use_case = SupplierUseCase(request=request)
        return use_case.get()


class SupplierByIdView(views.APIView):
    authentication_classes = [BellartiAuthenticationMiddleware]

    def get(self, request, id):
        use_case = SupplierUseCase(id=id)
        return use_case.get_by_id()

    def patch(self, request, id):
        use_case = SupplierUseCase(data=request.data, id=id)
        return use_case.update()

    def delete(self, request, id):
        use_case = SupplierUseCase(id=id)
        return use_case.delete()
