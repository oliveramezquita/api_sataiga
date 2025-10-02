from django.urls import re_path
from api_sataiga.handlers.kafka_consumer import NotificationConsumer

websocket_urlpatterns = [
    re_path(r'^ws/?$', NotificationConsumer.as_asgi()
            ),              # /ws o /ws/
    re_path(r'^ws/(?P<room_name>\w+)/?$',
            NotificationConsumer.as_asgi()),  # /ws/loquesea
]
