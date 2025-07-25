from rest_framework import views
from api.use_cases.inventory_use_case import InventoryUseCase
from api.middlewares import BellartiAuthenticationMiddleware


class InventoryView(views.APIView):
    authentication_classes = [BellartiAuthenticationMiddleware]

    def get(self, request):
        use_case = InventoryUseCase(request=request)
        return use_case.get()


class InventoryItemView(views.APIView):
    authentication_classes = [BellartiAuthenticationMiddleware]

    def get(self, request, id):
        use_case = InventoryUseCase(id=id)
        return use_case.get_by_id()
