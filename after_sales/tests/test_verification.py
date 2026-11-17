from datetime import timedelta

from django.test import override_settings
from django.urls import reverse

from after_sales.constants import STATUS_ACTIVE, STATUS_PENDING
from after_sales.helpers.timeutils import utcnow
from after_sales.helpers.tokens import decode_token
from after_sales.tests.base import AuthTestCase

SEND_URL = reverse("as-auth-verification-send")
CONFIRM_URL = reverse("as-auth-verification-confirm")


class VerificationSendTests(AuthTestCase):
    def test_send_activation_code(self):
        self.seed_auth(status=STATUS_PENDING)
        res = self.client.post(
            SEND_URL,
            {"identifier": "cliente@example.com", "purpose": "activation"},
            format="json",
        )
        self.assertEqual(res.status_code, 200)
        self.assertTrue(res.json()["sent"])
        self.assertEqual(len(self.sms.sent), 1)
        self.assertEqual(self.sms.sent[0]["phone"], "+5213331112233")
        records = self.rows("auth_verification")
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]["verification_type"], "activation")
        self.assertNotEqual(records[0]["code"], self.sms.last_code)  # hashed

    def test_send_activation_rejected_when_already_active(self):
        self.seed_active_auth()
        res = self.client.post(
            SEND_URL,
            {"identifier": "cliente@example.com", "purpose": "activation"},
            format="json",
        )
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json()["code"], "already_active")

    def test_send_login_code_for_unknown_device(self):
        self.seed_active_auth()
        res = self.client.post(
            SEND_URL,
            {
                "identifier": "cliente@example.com",
                "purpose": "login",
                "device_id": "device-xyz",
            },
            format="json",
        )
        self.assertEqual(res.status_code, 200)
        self.assertEqual(self.rows("auth_verification")[0]["device_id"], "device-xyz")

    def test_send_login_rejected_for_known_device(self):
        auth = self.seed_active_auth()
        self.store.setdefault("auth_device", []).append(
            {"auth_id": auth["_id"], "device_id": "device-known", "trusted": True}
        )
        res = self.client.post(
            SEND_URL,
            {
                "identifier": "cliente@example.com",
                "purpose": "login",
                "device_id": "device-known",
            },
            format="json",
        )
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json()["code"], "device_known")

    def test_send_login_requires_device_id(self):
        self.seed_active_auth()
        res = self.client.post(
            SEND_URL,
            {"identifier": "cliente@example.com", "purpose": "login"},
            format="json",
        )
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json()["code"], "device_id_required")

    @override_settings(AUTH_SMS_RESEND_COOLDOWN=timedelta(seconds=60))
    def test_resend_hits_cooldown(self):
        self.seed_auth(status=STATUS_PENDING)
        payload = {"identifier": "cliente@example.com", "purpose": "activation"}
        first = self.client.post(SEND_URL, payload, format="json")
        self.assertEqual(first.status_code, 200)
        second = self.client.post(SEND_URL, payload, format="json")
        self.assertEqual(second.status_code, 429)
        self.assertEqual(second.json()["code"], "resend_cooldown")


class VerificationConfirmTests(AuthTestCase):
    def test_confirm_activation_returns_activation_token(self):
        auth = self.seed_auth(status=STATUS_PENDING)
        self.seed_verification(auth_id=auth["_id"], code="654321")
        res = self.client.post(
            CONFIRM_URL,
            {
                "identifier": "cliente@example.com",
                "purpose": "activation",
                "code": "654321",
            },
            format="json",
        )
        self.assertEqual(res.status_code, 200)
        body = res.json()
        self.assertTrue(body["verified"])
        payload = decode_token(body["activation_token"], expected_type="activation")
        self.assertEqual(payload["sub"], auth["_id"])
        self.assertTrue(self.rows("auth_verification")[0]["verified"])

    def test_confirm_wrong_code_increments_attempts(self):
        auth = self.seed_auth(status=STATUS_PENDING)
        record = self.seed_verification(auth_id=auth["_id"], code="111111")
        res = self.client.post(
            CONFIRM_URL,
            {
                "identifier": "cliente@example.com",
                "purpose": "activation",
                "code": "000000",
            },
            format="json",
        )
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json()["code"], "invalid_code")
        self.assertEqual(self.verification_row(record["_id"])["attempts"], 1)

    def test_confirm_expired_code(self):
        auth = self.seed_auth(status=STATUS_PENDING)
        self.seed_verification(
            auth_id=auth["_id"],
            code="222222",
            sent_at=utcnow() - timedelta(minutes=30),
            expires_at=utcnow() - timedelta(minutes=20),
        )
        res = self.client.post(
            CONFIRM_URL,
            {
                "identifier": "cliente@example.com",
                "purpose": "activation",
                "code": "222222",
            },
            format="json",
        )
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json()["code"], "code_expired")

    def test_confirm_exhausted_attempts(self):
        auth = self.seed_auth(status=STATUS_PENDING)
        self.seed_verification(auth_id=auth["_id"], code="333333", attempts=5)
        res = self.client.post(
            CONFIRM_URL,
            {
                "identifier": "cliente@example.com",
                "purpose": "activation",
                "code": "333333",
            },
            format="json",
        )
        self.assertEqual(res.status_code, 429)
        self.assertEqual(res.json()["code"], "code_attempts_exceeded")

    def test_confirm_without_pending_verification(self):
        self.seed_auth(status=STATUS_PENDING)
        res = self.client.post(
            CONFIRM_URL,
            {
                "identifier": "cliente@example.com",
                "purpose": "activation",
                "code": "999999",
            },
            format="json",
        )
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json()["code"], "verification_not_found")

    def test_confirm_login_registers_device_and_issues_tokens(self):
        auth = self.seed_active_auth()
        self.seed_verification(
            auth_id=auth["_id"],
            verification_type="login",
            code="424242",
            device_id="device-new",
        )
        res = self.client.post(
            CONFIRM_URL,
            {
                "identifier": "cliente@example.com",
                "purpose": "login",
                "code": "424242",
                "device_name": "Pixel 8",
                "device_type": "android",
            },
            format="json",
        )
        self.assertEqual(res.status_code, 200)
        body = res.json()
        self.assertIn("access", body)
        self.assertIn("refresh", body)
        devices = self.rows("auth_device")
        self.assertEqual(len(devices), 1)
        self.assertEqual(devices[0]["device_id"], "device-new")
        self.assertTrue(devices[0]["trusted"])
        access = decode_token(body["access"], expected_type="access")
        self.assertEqual(access["sub"], auth["_id"])
