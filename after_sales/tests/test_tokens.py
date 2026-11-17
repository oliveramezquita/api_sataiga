from django.urls import reverse

from after_sales.constants import STATUS_DISABLED
from after_sales.helpers.tokens import decode_token, issue_token_pair
from after_sales.tests.base import AuthTestCase

REFRESH_URL = reverse("as-auth-token-refresh")
LOGOUT_URL = reverse("as-auth-logout")


class TokenRefreshTests(AuthTestCase):
    def _pair(self, auth):
        return issue_token_pair(auth)

    def test_refresh_returns_new_pair(self):
        auth = self.seed_active_auth()
        pair = self._pair(auth)
        res = self.client.post(
            REFRESH_URL, {"refresh": pair["refresh"]}, format="json"
        )
        self.assertEqual(res.status_code, 200)
        body = res.json()
        self.assertIn("access", body)
        self.assertIn("refresh", body)
        decode_token(body["access"], expected_type="access")

    def test_refresh_rejects_access_token(self):
        auth = self.seed_active_auth()
        pair = self._pair(auth)
        res = self.client.post(
            REFRESH_URL, {"refresh": pair["access"]}, format="json"
        )
        self.assertEqual(res.status_code, 401)
        self.assertEqual(res.json()["code"], "token_invalid")

    def test_refresh_rejects_revoked_token(self):
        auth = self.seed_active_auth()
        pair = self._pair(auth)
        self.client.post(LOGOUT_URL, {"refresh": pair["refresh"]}, format="json")
        res = self.client.post(
            REFRESH_URL, {"refresh": pair["refresh"]}, format="json"
        )
        self.assertEqual(res.status_code, 401)
        self.assertEqual(res.json()["code"], "token_revoked")

    def test_refresh_rotates_old_token(self):
        auth = self.seed_active_auth()
        pair = self._pair(auth)
        first = self.client.post(
            REFRESH_URL, {"refresh": pair["refresh"]}, format="json"
        )
        self.assertEqual(first.status_code, 200)
        # el refresh original ya no sirve
        again = self.client.post(
            REFRESH_URL, {"refresh": pair["refresh"]}, format="json"
        )
        self.assertEqual(again.status_code, 401)
        # el nuevo sí
        rotated = self.client.post(
            REFRESH_URL, {"refresh": first.json()["refresh"]}, format="json"
        )
        self.assertEqual(rotated.status_code, 200)

    def test_refresh_rejected_for_non_active_account(self):
        auth = self.seed_active_auth()
        pair = self._pair(auth)
        self.auth_row(auth["_id"])["status"] = STATUS_DISABLED
        res = self.client.post(
            REFRESH_URL, {"refresh": pair["refresh"]}, format="json"
        )
        self.assertEqual(res.status_code, 401)
        self.assertEqual(res.json()["code"], "invalid_session")


class LogoutTests(AuthTestCase):
    def test_logout_blacklists_refresh(self):
        auth = self.seed_active_auth()
        pair = issue_token_pair(auth)
        res = self.client.post(
            LOGOUT_URL, {"refresh": pair["refresh"]}, format="json"
        )
        self.assertEqual(res.status_code, 200)
        self.assertTrue(res.json()["success"])
        self.assertEqual(len(self.rows("auth_token_blacklist")), 1)

    def test_logout_is_idempotent_with_bad_token(self):
        res = self.client.post(
            LOGOUT_URL, {"refresh": "not-a-real-token"}, format="json"
        )
        self.assertEqual(res.status_code, 200)
        self.assertTrue(res.json()["success"])
        self.assertEqual(self.rows("auth_token_blacklist"), [])
