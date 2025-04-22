import asyncio
import websockets
from kafka import KafkaConsumer
import json

consumer = KafkaConsumer(
    'notifications',
    bootstrap_servers='localhost:9092',
    value_deserializer=lambda m: json.loads(m.decode('utf-8'))
)

clients = set()


async def notify_clients():
    for msg in consumer:
        data = msg.value
        if clients:
            await asyncio.wait([client.send(json.dumps(data)) for client in clients])


async def handler(websocket, path):
    clients.add(websocket)
    try:
        await websocket.wait_closed()
    finally:
        clients.remove(websocket)

start_server = websockets.serve(handler, '0.0.0.0', 8765)

loop = asyncio.get_event_loop()
loop.run_until_complete(start_server)
loop.create_task(notify_clients())
loop.run_forever()
