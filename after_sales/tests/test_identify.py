from django.urls import reverse

from after_sales.constants import (
    STATUS_ACTIVE,
    STATUS_DISABLED,
    STATUS_LOCKED,
    STATUS_PENDING,
)
from after_sales.tests.base import AuthTestCase


class IdentifyTests(AuthTestCase):
    url = reverse("as-auth-identify")

    def test_unknown_identifier_returns_404(self):
        res = self.client.post(
            self.url, {"identifier": "nadie@example.com"}, format="json"
        )
        self.assertEqual(res.status_code, 404)
        self.assertEqual(res.json()["code"], "account_not_found")

    def test_pending_account_routes_to_first_access(self):
        self.seed_auth(status=STATUS_PENDING)
        res = self.client.post(
            self.url, {"identifier": "cliente@example.com"}, format="json"
        )
        self.assertEqual(res.status_code, 200)
        body = res.json()
        self.assertEqual(body["status"], STATUS_PENDING)
        self.assertEqual(body["next"], "first_access")
        self.assertEqual(body["identifier_type"], "email")
        self.assertFalse(body["has_password"])

    def test_active_account_routes_to_login(self):
        self.seed_active_auth()
        res = self.client.post(
            self.url, {"identifier": "+5213331112233"}, format="json"
        )
        self.assertEqual(res.status_code, 200)
        body = res.json()
        self.assertEqual(body["status"], STATUS_ACTIVE)
        self.assertEqual(body["next"], "login")
        self.assertEqual(body["identifier_type"], "phone")
        self.assertTrue(body["has_password"])

    def test_locked_account_routes_to_locked(self):
        self.seed_auth(status=STATUS_LOCKED)
        res = self.client.post(
            self.url, {"identifier": "cliente@example.com"}, format="json"
        )
        self.assertEqual(res.json()["next"], "locked")

    def test_disabled_account_routes_to_disabled(self):
        self.seed_auth(status=STATUS_DISABLED)
        res = self.client.post(
            self.url, {"identifier": "cliente@example.com"}, format="json"
        )
        self.assertEqual(res.json()["next"], "disabled")

    def test_garbage_identifier_returns_400(self):
        res = self.client.post(
            self.url, {"identifier": "not-an-email-or-phone"}, format="json"
        )
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json()["code"], "invalid_identifier")

    def test_missing_identifier_returns_400(self):
        res = self.client.post(self.url, {}, format="json")
        self.assertEqual(res.status_code, 400)
