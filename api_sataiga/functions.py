import jwt  # type: ignore
import json
from mail_templated import send_mail
from django.conf import settings
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from api_sataiga.handlers.mongodb_handler import MongoDBHandler
from api.serializers.notification_serializer import NotificationSerializer


def encode_user(user):
    encoded_data = jwt.encode(
        payload=user, key=settings.AUTH_SECRET, algorithm="HS256")
    return encoded_data


def decode_user(token):
    decoded_data = jwt.decode(
        jwt=token, key=settings.AUTH_SECRET, algorithms=["HS256"])
    return decoded_data


def hex_encode(data):
    json_data = json.dumps(data)
    json_bytes = json_data.encode('utf-8')
    return json_bytes.hex()


def hex_decode(data):
    decoded_bytes = bytes.fromhex(data)
    decoded_json_data = decoded_bytes.decode('utf-8')
    return json.loads(decoded_json_data)


def send_email(template, context):
    to = []
    to.append(context['email'])
    send_mail(
        template_name=template,
        context=context,
        from_email='Sistema Bellarti <info@bellarti.art>',
        recipient_list=to
    )


def insert_notification(message):
    with MongoDBHandler('notifications') as db:
        notification_id = db.insert({**message})
        notification = db.extract({'_id': notification_id})
    return NotificationSerializer(notification[0]).data


def send_notification(message):
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        "notifications",
        {
            "type": "notify",
            "message": insert_notification(message)
        }
    )
