from rest_framework import views
from api.use_cases.bank_data_use_case import BankDataUseCase
from api.middlewares import BellartiAuthenticationMiddleware


class BankDataView(views.APIView):
    authentication_classes = [BellartiAuthenticationMiddleware]

    def post(self, request, supplier_id):
        use_case = BankDataUseCase(data=request.data, supplier_id=supplier_id)
        return use_case.save()

    def get(self, request, supplier_id):
        use_case = BankDataUseCase(supplier_id=supplier_id)
        return use_case.get_by_supplier()
