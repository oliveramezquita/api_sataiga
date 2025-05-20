from rest_framework import views
from api.middlewares import BellartiAuthenticationMiddleware
from api.use_cases.quantification_use_case import QuantificationUseCase


class QuantificationView(views.APIView):
    authentication_classes = [BellartiAuthenticationMiddleware]

    def get(self, request):
        use_case = QuantificationUseCase(request=request)
        return use_case.get()


class QuantificationFiltersView(views.APIView):
    authentication_classes = [BellartiAuthenticationMiddleware]

    def get(self, request):
        use_case = QuantificationUseCase(request=request)
        return use_case.filters()


class QuantificationByIdView(views.APIView):
    authentication_classes = [BellartiAuthenticationMiddleware]

    def patch(self, request, id, action):
        use_case = QuantificationUseCase(
            data=request.data, id=id, action=action)
        return use_case.update()
