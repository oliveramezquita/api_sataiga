from datetime import timedelta

from django.urls import reverse

from after_sales.constants import STATUS_DISABLED, STATUS_PENDING
from after_sales.helpers.passwords import verify_password
from after_sales.helpers.timeutils import utcnow
from after_sales.tests.base import VALID_PASSWORD, AuthTestCase

REQUEST_URL = reverse("as-auth-password-reset-request")
CONFIRM_URL = reverse("as-auth-password-reset-confirm")
NEW_PASSWORD = "Rese7-Pass-w0rd"


class PasswordResetRequestTests(AuthTestCase):
    def test_request_sends_sms_code(self):
        self.seed_active_auth()
        res = self.client.post(
            REQUEST_URL, {"identifier": "cliente@example.com"}, format="json"
        )
        self.assertEqual(res.status_code, 200)
        self.assertTrue(res.json()["sent"])
        self.assertEqual(len(self.sms.sent), 1)
        self.assertEqual(
            self.rows("auth_verification")[0]["verification_type"],
            "password_reset",
        )

    def test_request_unknown_identifier_returns_404(self):
        res = self.client.post(
            REQUEST_URL, {"identifier": "ghost@example.com"}, format="json"
        )
        self.assertEqual(res.status_code, 404)

    def test_request_rejected_for_pending_account(self):
        self.seed_auth(status=STATUS_PENDING)
        res = self.client.post(
            REQUEST_URL, {"identifier": "cliente@example.com"}, format="json"
        )
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json()["code"], "activation_required")


class PasswordResetConfirmTests(AuthTestCase):
    def test_confirm_updates_password(self):
        auth = self.seed_active_auth()
        self.seed_verification(
            auth_id=auth["_id"],
            verification_type="password_reset",
            code="778899",
        )
        res = self.client.post(
            CONFIRM_URL,
            {
                "identifier": "cliente@example.com",
                "code": "778899",
                "password": NEW_PASSWORD,
                "confirm_password": NEW_PASSWORD,
            },
            format="json",
        )
        self.assertEqual(res.status_code, 200)
        row = self.auth_row(auth["_id"])
        self.assertTrue(verify_password(NEW_PASSWORD, row["password"]))
        self.assertFalse(verify_password(VALID_PASSWORD, row["password"]))

    def test_confirm_wrong_code(self):
        auth = self.seed_active_auth()
        self.seed_verification(
            auth_id=auth["_id"],
            verification_type="password_reset",
            code="111000",
        )
        res = self.client.post(
            CONFIRM_URL,
            {
                "identifier": "cliente@example.com",
                "code": "000111",
                "password": NEW_PASSWORD,
            },
            format="json",
        )
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json()["code"], "invalid_code")

    def test_confirm_expired_code(self):
        auth = self.seed_active_auth()
        self.seed_verification(
            auth_id=auth["_id"],
            verification_type="password_reset",
            code="121212",
            sent_at=utcnow() - timedelta(minutes=30),
            expires_at=utcnow() - timedelta(minutes=20),
        )
        res = self.client.post(
            CONFIRM_URL,
            {
                "identifier": "cliente@example.com",
                "code": "121212",
                "password": NEW_PASSWORD,
            },
            format="json",
        )
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json()["code"], "code_expired")

    def test_confirm_does_not_reactivate_disabled_account(self):
        auth = self.seed_active_auth(status=STATUS_DISABLED)
        self.seed_verification(
            auth_id=auth["_id"],
            verification_type="password_reset",
            code="343434",
        )
        res = self.client.post(
            CONFIRM_URL,
            {
                "identifier": "cliente@example.com",
                "code": "343434",
                "password": NEW_PASSWORD,
            },
            format="json",
        )
        self.assertEqual(res.status_code, 200)
        self.assertEqual(self.auth_row(auth["_id"])["status"], STATUS_DISABLED)
