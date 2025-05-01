from rest_framework import views
from api.use_cases.explosion_use_case import ExplosionUseCase
from api.middlewares import BellartiAuthenticationMiddleware


class ExplosionView(views.APIView):
    authentication_classes = [BellartiAuthenticationMiddleware]

    def get(self, request, home_production_id):
        use_case = ExplosionUseCase(
            request=request, home_production_id=home_production_id)
        return use_case.get()
