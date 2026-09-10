from rest_framework import views
from api.use_cases.after_sales_use_case import AfterSalesUseCase
from api.middlewares import BellartiAuthenticationMiddleware


class SendInvitationView(views.APIView):
    authentication_classes = [BellartiAuthenticationMiddleware]

    def get(self, request):
        use_case = AfterSalesUseCase(request=request)
        return use_case.send_invitation()
