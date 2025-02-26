import jwt  # type: ignore
import json
from mail_templated import send_mail
from django.conf import settings


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
