from datetime import timedelta

from django.test import override_settings
from django.urls import reverse

from after_sales.constants import STATUS_ACTIVE, STATUS_PENDING
from after_sales.helpers.passwords import verify_password
from after_sales.helpers.tokens import issue_onboarding_token
from after_sales.tests.base import VALID_PASSWORD, AuthTestCase

URL = reverse("as-auth-activate")


class ActivateTests(AuthTestCase):
    def _token(self, auth):
        return issue_onboarding_token(auth, "activation")

    def test_activate_sets_password_and_status_active(self):
        auth = self.seed_auth(status=STATUS_PENDING)
        res = self.client.post(
            URL,
            {
                "activation_token": self._token(auth),
                "password": VALID_PASSWORD,
                "confirm_password": VALID_PASSWORD,
                "device_id": "device-1",
                "device_type": "ios",
                "biometric_enabled": True,
            },
            format="json",
        )
        self.assertEqual(res.status_code, 200)
        body = res.json()
        self.assertTrue(body["activated"])
        self.assertIn("access", body)

        row = self.auth_row(auth["_id"])
        self.assertEqual(row["status"], STATUS_ACTIVE)
        self.assertTrue(verify_password(VALID_PASSWORD, row["password"]))
        self.assertIsNotNone(row["activated_at"])

        device = self.rows("auth_device")[0]
        self.assertTrue(device["biometric_enabled"])

    def test_activate_rejects_invalid_token(self):
        self.seed_auth(status=STATUS_PENDING)
        res = self.client.post(
            URL,
            {"activation_token": "garbage.token.value", "password": VALID_PASSWORD},
            format="json",
        )
        self.assertEqual(res.status_code, 401)
        self.assertEqual(res.json()["code"], "token_invalid")

    @override_settings(AUTH_ONBOARDING_TOKEN_LIFETIME=timedelta(seconds=-1))
    def test_activate_rejects_expired_token(self):
        auth = self.seed_auth(status=STATUS_PENDING)
        res = self.client.post(
            URL,
            {"activation_token": self._token(auth), "password": VALID_PASSWORD},
            format="json",
        )
        self.assertEqual(res.status_code, 401)
        self.assertEqual(res.json()["code"], "token_expired")

    def test_activate_rejects_weak_password(self):
        auth = self.seed_auth(status=STATUS_PENDING)
        res = self.client.post(
            URL,
            {"activation_token": self._token(auth), "password": "12345678"},
            format="json",
        )
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json()["code"], "weak_password")

    def test_activate_rejects_password_mismatch(self):
        auth = self.seed_auth(status=STATUS_PENDING)
        res = self.client.post(
            URL,
            {
                "activation_token": self._token(auth),
                "password": VALID_PASSWORD,
                "confirm_password": "something-else-9",
            },
            format="json",
        )
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json()["code"], "password_mismatch")

    def test_activate_rejects_already_active_account(self):
        auth = self.seed_active_auth()
        res = self.client.post(
            URL,
            {"activation_token": self._token(auth), "password": VALID_PASSWORD},
            format="json",
        )
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json()["code"], "already_active")
