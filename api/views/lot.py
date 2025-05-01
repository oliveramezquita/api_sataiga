from rest_framework import views
from api.use_cases.lot_use_case import LotUseCase
from api.middlewares import BellartiAuthenticationMiddleware


class LotsView(views.APIView):
    authentication_classes = [BellartiAuthenticationMiddleware]

    def post(self, request, home_production_id):
        use_case = LotUseCase(
            data=request.data, home_production_id=home_production_id)
        return use_case.save()

    def get(self, request, home_production_id):
        use_case = LotUseCase(home_production_id=home_production_id)
        return use_case.get()


class LotView(views.APIView):
    authentication_classes = [BellartiAuthenticationMiddleware]

    def patch(self, request, id):
        use_case = LotUseCase(data=request.data, id=id)
        return use_case.update()

    def delete(self, request, id):
        use_case = LotUseCase(id=id)
        return use_case.delete()
