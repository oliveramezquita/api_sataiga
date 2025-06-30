from rest_framework import views
from api.use_cases.purchase_order_use_case import PurchaseOrderUseCase
from api.middlewares import BellartiAuthenticationMiddleware


class PurchaseOrdersView(views.APIView):
    authentication_classes = [BellartiAuthenticationMiddleware]

    def post(self, request):
        use_case = PurchaseOrderUseCase(data=request.data)
        return use_case.save()

    def get(self, request):
        use_case = PurchaseOrderUseCase(request=request)
        return use_case.get()


class PurchaseOrderView(views.APIView):
    authentication_classes = [BellartiAuthenticationMiddleware]

    def get(self, request, id):
        use_case = PurchaseOrderUseCase(id=id)
        return use_case.get_by_id()

    def put(self, request, id):
        use_case = PurchaseOrderUseCase(id=id, data=request.data)
        return use_case.update()

    def patch(self, request, id):
        use_case = PurchaseOrderUseCase(id=id, data=request.data)
        return use_case.modify()

    def delete(self, request, id):
        use_case = PurchaseOrderUseCase(id=id)
        return use_case.delete()


class ProjectsView(views.APIView):
    authentication_classes = [BellartiAuthenticationMiddleware]

    def get(self, request):
        use_case = PurchaseOrderUseCase()
        return use_case.get_projects()


class PurchaseOrderSuppliersView(views.APIView):
    authentication_classes = [BellartiAuthenticationMiddleware]

    def get(self, request, home_production_id):
        use_case = PurchaseOrderUseCase(home_production_id=home_production_id)
        return use_case.get_suppliers()


class PurchaseOrderMaterialsView(views.APIView):
    authentication_classes = [BellartiAuthenticationMiddleware]

    def get(self, request, home_production_id, supplier_id):
        use_case = PurchaseOrderUseCase(
            home_production_id=home_production_id, supplier_id=supplier_id)
        return use_case.get_materials()


class InputRegisterView(views.APIView):
    authentication_classes = [BellartiAuthenticationMiddleware]

    def patch(self, request, id):
        use_case = PurchaseOrderUseCase(id=id, data=request.data)
        return use_case.input_register()
