import jwt  # type: ignore
import json
from .settings import AUTH_SECRET


def encode_user(user):
    encoded_data = jwt.encode(payload=user, key=AUTH_SECRET, algorithm="HS256")
    return encoded_data


def decode_user(token):
    decoded_data = jwt.decode(jwt=token, key=AUTH_SECRET, algorithms=["HS256"])
    return decoded_data


def hex_encode(data):
    json_data = json.dumps(data)
    json_bytes = json_data.encode('utf-8')
    return json_bytes.hex()


def hex_decode(data):
    decoded_bytes = bytes.fromhex(data)
    decoded_json_data = decoded_bytes.decode('utf-8')
    return json.loads(decoded_json_data)
