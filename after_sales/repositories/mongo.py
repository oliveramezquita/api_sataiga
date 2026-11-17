"""
Único punto de acceso a MongoDB para el flujo de autenticación.

Todo pasa por el handler compartido `api_sataiga.handlers.mongodb_handler`
(no se usan llamadas directas a pymongo). En las pruebas se parchea
`MongoDBHandler` en este módulo con un doble en memoria.
"""
from bson import ObjectId
from bson.errors import InvalidId

from api_sataiga.handlers.mongodb_handler import MongoDBHandler

from after_sales.constants import (
    COLLECTION_AUTH,
    COLLECTION_DEVICE,
    COLLECTION_TOKEN_BLACKLIST,
    COLLECTION_VERIFICATION,
)
from after_sales.helpers.timeutils import utcnow


def oid(value):
    """ObjectId(value) tolerante: si no es un ObjectId válido, lo deja igual.

    En producción `auth._id` / `auth.user_id` son ObjectId; en pruebas son
    strings. Con esto ambos caminos funcionan.
    """
    if isinstance(value, ObjectId):
        return value
    try:
        return ObjectId(value)
    except (InvalidId, TypeError):
        return value


class AuthRepository:
    collection = COLLECTION_AUTH

    def _find_one(self, query):
        with MongoDBHandler(self.collection) as db:
            rows = db.extract(query)
            return rows[0] if rows else None

    def find_by_identifier(self, kind, value):
        field = "email" if kind == "email" else "phone"
        return self._find_one({field: value})

    def find_by_id(self, _id):
        return self._find_one({"_id": oid(_id)})

    def update(self, _id, data):
        with MongoDBHandler(self.collection) as db:
            return db.update({"_id": oid(_id)}, data)


class VerificationRepository:
    collection = COLLECTION_VERIFICATION

    def create(self, data):
        with MongoDBHandler(self.collection) as db:
            return db.insert(data)

    def latest(self, auth_id, verification_type, only_pending=False):
        query = {
            "auth_id": str(auth_id),
            "verification_type": verification_type,
        }
        if only_pending:
            query["verified"] = False
        with MongoDBHandler(self.collection) as db:
            rows = db.extract(query, order_field="sent_at", order=-1)
            return rows[0] if rows else None

    def latest_pending(self, auth_id, verification_type):
        return self.latest(auth_id, verification_type, only_pending=True)

    def increment_attempts(self, _id):
        with MongoDBHandler(self.collection) as db:
            return db.update({"_id": oid(_id)}, {"$inc": {"attempts": 1}})

    def mark_verified(self, _id):
        with MongoDBHandler(self.collection) as db:
            return db.update(
                {"_id": oid(_id)},
                {"verified": True, "verified_at": utcnow()},
            )


class DeviceRepository:
    collection = COLLECTION_DEVICE

    def find(self, auth_id, device_id):
        with MongoDBHandler(self.collection) as db:
            rows = db.extract(
                {"auth_id": str(auth_id), "device_id": device_id}
            )
            return rows[0] if rows else None

    def is_known(self, auth_id, device_id):
        if not device_id:
            return False
        return self.find(auth_id, device_id) is not None

    def register(self, auth_id, device_id, name=None, device_type=None,
                 biometric=False):
        now = utcnow()
        with MongoDBHandler(self.collection) as db:
            return db.update(
                {"auth_id": str(auth_id), "device_id": device_id},
                {
                    "$set": {
                        "auth_id": str(auth_id),
                        "device_id": device_id,
                        "device_name": name,
                        "device_type": device_type,
                        "biometric_enabled": bool(biometric),
                        "trusted": True,
                        "verified_at": now,
                        "last_login": now,
                    }
                },
                upsert=True,
            )

    def touch(self, auth_id, device_id, ip=None):
        if not device_id:
            return None
        with MongoDBHandler(self.collection) as db:
            return db.update(
                {"auth_id": str(auth_id), "device_id": device_id},
                {"last_login": utcnow(), "last_login_ip": ip},
            )


class TokenBlacklistRepository:
    collection = COLLECTION_TOKEN_BLACKLIST

    def add(self, jti, expires_at):
        if not jti:
            return None
        with MongoDBHandler(self.collection) as db:
            return db.insert({"jti": jti, "expires_at": expires_at})

    def contains(self, jti):
        if not jti:
            return False
        with MongoDBHandler(self.collection) as db:
            return bool(db.extract({"jti": jti}))
