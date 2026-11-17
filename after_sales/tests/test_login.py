from django.test import override_settings
from django.urls import reverse

from after_sales.constants import (
    STATUS_DISABLED,
    STATUS_LOCKED,
    STATUS_PENDING,
)
from after_sales.helpers.tokens import decode_token
from after_sales.tests.base import VALID_PASSWORD, AuthTestCase

URL = reverse("as-auth-login")


class LoginStatusGateTests(AuthTestCase):
    def _login(self, **extra):
        payload = {
            "identifier": "cliente@example.com",
            "password": VALID_PASSWORD,
        }
        payload.update(extra)
        return self.client.post(URL, payload, format="json")

    def test_pending_account_rejected(self):
        self.seed_auth(status=STATUS_PENDING, password=None)
        res = self._login()
        self.assertEqual(res.status_code, 403)
        self.assertEqual(res.json()["code"], "activation_required")

    def test_locked_account_rejected(self):
        self.seed_active_auth(status=STATUS_LOCKED)
        res = self._login()
        self.assertEqual(res.status_code, 403)
        self.assertEqual(res.json()["code"], "account_locked")

    def test_disabled_account_rejected(self):
        self.seed_active_auth(status=STATUS_DISABLED)
        res = self._login()
        self.assertEqual(res.status_code, 403)
        self.assertEqual(res.json()["code"], "account_disabled")

    def test_unknown_identifier_is_generic(self):
        res = self._login()
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json()["code"], "invalid_credentials")


class LoginPasswordTests(AuthTestCase):
    def test_wrong_password_increments_failed_attempts(self):
        auth = self.seed_active_auth()
        res = self.client.post(
            URL,
            {"identifier": "cliente@example.com", "password": "wrong-pass-1"},
            format="json",
        )
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json()["code"], "invalid_credentials")
        self.assertEqual(self.auth_row(auth["_id"])["failed_login_attempts"], 1)

    @override_settings(AUTH_MAX_FAILED_ATTEMPTS=5)
    def test_lockout_transition_after_threshold(self):
        auth = self.seed_active_auth(failed_login_attempts=4)
        res = self.client.post(
            URL,
            {"identifier": "cliente@example.com", "password": "still-wrong-1"},
            format="json",
        )
        self.assertEqual(res.status_code, 403)
        self.assertEqual(res.json()["code"], "account_disabled")
        row = self.auth_row(auth["_id"])
        self.assertEqual(row["status"], STATUS_DISABLED)
        self.assertEqual(row["failed_login_attempts"], 5)

    def test_login_with_known_device_issues_tokens(self):
        auth = self.seed_active_auth(failed_login_attempts=3)
        self.store.setdefault("auth_device", []).append(
            {"auth_id": auth["_id"], "device_id": "device-ok", "trusted": True}
        )
        res = self.client.post(
            URL,
            {
                "identifier": "cliente@example.com",
                "password": VALID_PASSWORD,
                "device_id": "device-ok",
            },
            format="json",
        )
        self.assertEqual(res.status_code, 200)
        body = res.json()
        self.assertIn("access", body)
        self.assertIn("refresh", body)
        self.assertEqual(body["user"]["id"], auth["_id"])
        # el contador de fallidos se limpia en un login exitoso
        self.assertEqual(self.auth_row(auth["_id"])["failed_login_attempts"], 0)
        decode_token(body["refresh"], expected_type="refresh")

    def test_login_without_device_id_issues_tokens(self):
        self.seed_active_auth()
        res = self.client.post(
            URL,
            {"identifier": "cliente@example.com", "password": VALID_PASSWORD},
            format="json",
        )
        self.assertEqual(res.status_code, 200)
        self.assertIn("access", res.json())

    def test_login_with_unknown_device_triggers_2fa(self):
        self.seed_active_auth()
        res = self.client.post(
            URL,
            {
                "identifier": "cliente@example.com",
                "password": VALID_PASSWORD,
                "device_id": "brand-new-device",
            },
            format="json",
        )
        self.assertEqual(res.status_code, 200)
        body = res.json()
        self.assertTrue(body["verification_required"])
        self.assertNotIn("access", body)
        self.assertEqual(len(self.sms.sent), 1)
        record = self.rows("auth_verification")[0]
        self.assertEqual(record["verification_type"], "login")
        self.assertEqual(record["device_id"], "brand-new-device")
