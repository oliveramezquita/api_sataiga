from rest_framework import views
from api.use_cases.notification_use_case import NotificationUseCase
from api.middlewares import BellartiAuthenticationMiddleware


class NotificationsView(views.APIView):
    authentication_classes = [BellartiAuthenticationMiddleware]

    def get(self, request):
        use_case = NotificationUseCase(request=request)
        return use_case.get()

    def patch(self, request):
        use_case = NotificationUseCase(data=request.data)
        return use_case.update()

    def delete(self, request):
        use_case = NotificationUseCase(data=request.data)
        return use_case.delete()
