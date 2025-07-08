from rest_framework import views
from api.use_cases.inventory_use_case import InventoryUseCase
from api.middlewares import BellartiAuthenticationMiddleware


class InventoryView(views.APIView):
    authentication_classes = [BellartiAuthenticationMiddleware]

    def get(self, request):
        use_case = InventoryUseCase(request=request)
        return use_case.get()
