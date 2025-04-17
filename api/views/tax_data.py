from rest_framework import views
from api.use_cases.tax_data_use_case import TaxDataUseCase
from api.middlewares import BellartiAuthenticationMiddleware


class TaxDataView(views.APIView):
    authentication_classes = [BellartiAuthenticationMiddleware]

    def post(self, request, supplier_id):
        use_case = TaxDataUseCase(data=request.data, supplier_id=supplier_id)
        return use_case.save()

    def get(self, request, supplier_id):
        use_case = TaxDataUseCase(supplier_id=supplier_id)
        return use_case.get_by_supplier()
