from rest_framework import views
from api.use_cases.dashboard_use_case import DashboardUseCase
from api.middlewares import BellartiAuthenticationMiddleware


class DashboardView(views.APIView):
    authentication_classes = [BellartiAuthenticationMiddleware]

    def get(self, request):
        use_case = DashboardUseCase()
        return use_case.get()
