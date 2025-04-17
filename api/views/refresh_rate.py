from rest_framework import views
from api.use_cases.refresh_rate_use_case import RefreshRateUseCase
from api.middlewares import BellartiAuthenticationMiddleware


class RefreshRateView(views.APIView):
    authentication_classes = [BellartiAuthenticationMiddleware]

    def post(self, request, supplier_id):
        use_case = RefreshRateUseCase(
            data=request.data, supplier_id=supplier_id)
        return use_case.save()

    def get(self, request, supplier_id):
        use_case = RefreshRateUseCase(supplier_id=supplier_id)
        return use_case.get_by_supplier()


class RefreshRatesView(views.APIView):
    authentication_classes = [BellartiAuthenticationMiddleware]

    def get(self, request):
        use_case = RefreshRateUseCase()
        return use_case.refresh_rates()
