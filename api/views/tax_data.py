from rest_framework import views
from api.use_cases.tax_data_use_case import TaxDataUseCase
from api.middlewares import BellartiAuthenticationMiddleware


class TaxDataSupplierView(views.APIView):
    authentication_classes = [BellartiAuthenticationMiddleware]

    def post(self, request, supplier_id):
        use_case = TaxDataUseCase(data=request.data, supplier_id=supplier_id)
        return use_case.save_by_supplier()

    def get(self, request, supplier_id):
        use_case = TaxDataUseCase(supplier_id=supplier_id)
        return use_case.get_by_supplier()


class TaxDataClientView(views.APIView):
    authentication_classes = [BellartiAuthenticationMiddleware]

    def post(self, request, client_id):
        use_case = TaxDataUseCase(data=request.data, client_id=client_id)
        return use_case.save_by_client()

    def get(self, request, client_id):
        use_case = TaxDataUseCase(client_id=client_id)
        return use_case.get_by_client()
