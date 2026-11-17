from datetime import timedelta
from unittest.mock import patch

from django.test import override_settings
from rest_framework.test import APITestCase

from after_sales.constants import STATUS_ACTIVE, STATUS_PENDING
from after_sales.helpers.passwords import hash_password
from after_sales.tests.fakes import CapturingSms, handler_factory, new_store

VALID_PASSWORD = "Str0ng-Pass-9"


@override_settings(
    # Sin cooldown por defecto; el test dedicado lo reactiva.
    AUTH_SMS_RESEND_COOLDOWN=timedelta(seconds=0),
    AFTER_SALES_SMS_BACKEND="after_sales.services.sms.ConsoleSmsBackend",
)
class AuthTestCase(APITestCase):
    def setUp(self):
        self.store = new_store()

        mongo_patch = patch(
            "after_sales.repositories.mongo.MongoDBHandler",
            side_effect=handler_factory(self.store),
        )
        mongo_patch.start()
        self.addCleanup(mongo_patch.stop)

        self.sms = CapturingSms()
        sms_patch = patch(
            "after_sales.use_cases.auth_use_case.send_verification_sms",
            new=self.sms,
        )
        sms_patch.start()
        self.addCleanup(sms_patch.stop)

    # -- helpers -------------------------------------------------------
    def seed_auth(self, **overrides):
        doc = {
            "_id": "auth-1",
            "user_id": "cust-1",
            "user_type": "customer",
            "email": "cliente@example.com",
            "phone": "+5213331112233",
            "password": None,
            "status": STATUS_PENDING,
            "failed_login_attempts": 0,
            "locked_until": None,
        }
        doc.update(overrides)
        self.store.setdefault("auth", []).append(doc)
        return doc

    def seed_active_auth(self, password=VALID_PASSWORD, **overrides):
        overrides.setdefault("status", STATUS_ACTIVE)
        overrides.setdefault("password", hash_password(password))
        return self.seed_auth(**overrides)

    def seed_verification(self, auth_id="auth-1", verification_type="activation",
                          code="123456", **overrides):
        from after_sales.helpers.otp import hash_code
        from after_sales.helpers.timeutils import utcnow

        now = utcnow()
        doc = {
            "_id": f"ver-{len(self.store.get('auth_verification', [])) + 1}",
            "auth_id": auth_id,
            "device_id": None,
            "verification_type": verification_type,
            "verification_method": "sms",
            "code": hash_code(code),
            "sent_at": now,
            "expires_at": now + timedelta(minutes=10),
            "attempts": 0,
            "verified": False,
            "verified_at": None,
        }
        doc.update(overrides)
        self.store.setdefault("auth_verification", []).append(doc)
        return doc

    def rows(self, collection):
        return self.store.get(collection, [])

    def verification_row(self, _id):
        return next(
            r for r in self.rows("auth_verification") if r["_id"] == _id
        )

    def auth_row(self, _id="auth-1"):
        return next(r for r in self.rows("auth") if r["_id"] == _id)
