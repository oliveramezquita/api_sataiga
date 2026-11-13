
import time

from django_redis import get_redis_connection

from api_sataiga.functions import (
    encode_refresh_token,
    decode_refresh_token,
)


class RefreshTokenService:

    PREFIX = "bellarti:auth:refresh:"

    # Ejecutar la renovación de forma atómica en Redis.
    ROTATE_SCRIPT = """
    local old_key = KEYS[1]
    local new_key = KEYS[2]

    local user_id = ARGV[1]
    local ttl = tonumber(ARGV[2])

    if redis.call('GET', old_key) ~= user_id then
        return 0
    end

    if redis.call('EXISTS', new_key) == 1 then
        return 0
    end

    redis.call('SET', new_key, user_id, 'EX', ttl)
    redis.call('DEL', old_key)

    return 1
    """

    @classmethod
    def _connection(cls):
        return get_redis_connection("default")

    @classmethod
    def _key(cls, jti):
        return f"{cls.PREFIX}{jti}"

    @staticmethod
    def _ttl(payload):
        return max(
            0,
            int(payload["exp"] - time.time())
        )

    @classmethod
    def register(cls, token):
        """
        Guarda un Refresh Token válido en Redis.
        """
        payload = decode_refresh_token(token)

        ttl = cls._ttl(payload)

        if ttl <= 0:
            return False

        return bool(
            cls._connection().set(
                cls._key(payload["jti"]),
                payload["sub"],
                ex=ttl,
                nx=True,
            )
        )

    @classmethod
    def refresh(cls, token):
        """
        Consume el token anterior y genera uno nuevo.
        Un Refresh Token solo puede renovarse una vez.

        Devuelve el nuevo token o None si el anterior
        ya fue consumido o revocado.
        """
        payload = decode_refresh_token(token)

        user_id = payload["sub"]

        new_token = encode_refresh_token({
            "_id": user_id
        })

        new_payload = decode_refresh_token(new_token)

        ttl = cls._ttl(new_payload)

        if ttl <= 0:
            return None

        result = cls._connection().eval(
            cls.ROTATE_SCRIPT,
            2,
            cls._key(payload["jti"]),
            cls._key(new_payload["jti"]),
            user_id,
            ttl,
        )

        if result != 1:
            return None

        return new_token

    @classmethod
    def revoke(cls, token):
        """
        Revoca un Refresh Token.
        """
        payload = decode_refresh_token(token)

        return bool(
            cls._connection().delete(
                cls._key(payload["jti"])
            )
        )
