import json
from channels.generic.websocket import AsyncWebsocketConsumer
from kafka import KafkaConsumer


class NotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()

    async def disconnect(self, close_code):
        pass

    async def receive(self, text_data):
        data = json.loads(text_data)
        await self.send(text_data=json.dumps({
            "message": f"Received: {data}"
        }))

# Consume mensajes de Kafka y envía notificaciones


def consume_from_kafka():
    consumer = KafkaConsumer(
        'notifications',
        bootstrap_servers=['localhost:9092'],
        auto_offset_reset='earliest',
        enable_auto_commit=True,
        group_id='notifications-group'
    )
    for message in consumer:
        # Procesar mensajes y enviarlos al WebSocket
        # Por ejemplo, guardar en MongoDB
        # MONGO_DB['notifications'].insert_one(
        #     {"notification": message.value.decode()})
