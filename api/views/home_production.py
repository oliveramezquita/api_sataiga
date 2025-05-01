from rest_framework import views
from api.use_cases.home_production_use_case import HomeProdcutionUseCase
from api.middlewares import BellartiAuthenticationMiddleware


class HomeProductionView(views.APIView):
    authentication_classes = [BellartiAuthenticationMiddleware]

    def post(self, request):
        use_case = HomeProdcutionUseCase(data=request.data)
        return use_case.save()

    def get(self, request):
        use_case = HomeProdcutionUseCase(request=request)
        return use_case.get()


class HomeProductionByIdView(views.APIView):
    authentication_classes = [BellartiAuthenticationMiddleware]

    def get(self, request, id):
        use_case = HomeProdcutionUseCase(id=id)
        return use_case.get_by_id()

    def patch(self, request, id):
        use_case = HomeProdcutionUseCase(data=request.data, id=id)
        return use_case.update()

    def delete(self, request, id):
        use_case = HomeProdcutionUseCase(id=id)
        return use_case.delete()
