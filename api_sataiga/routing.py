from django.urls import re_path
from api_sataiga.handlers.notification_consumer import NotificationConsumer

websocket_urlpatterns = [
    re_path(r"^ws/?$", NotificationConsumer.as_asgi()),
]
