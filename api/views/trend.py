from rest_framework import views
from api.use_cases.trend_use_case import TrendUseCase
from api.middlewares import BellartiAuthenticationMiddleware


class TrendsView(views.APIView):
    authentication_classes = [BellartiAuthenticationMiddleware]

    def get(self, request):
        use_case = TrendUseCase(request=request)
        return use_case.get()

    def post(self, request):
        use_case = TrendUseCase(data=request.data)
        return use_case.save()


class TrendByIdView(views.APIView):
    authentication_classes = [BellartiAuthenticationMiddleware]

    def get(self, request, id):
        use_case = TrendUseCase(id=id)
        return use_case.get_by_id()

    def delete(self, request, id):
        use_case = TrendUseCase(id=id)
        return use_case.delete()


class TrendElemetsView(views.APIView):
    authentication_classes = [BellartiAuthenticationMiddleware]

    def patch(self, request, id):
        use_case = TrendUseCase(data=request.data, id=id)
        return use_case.add_items()
