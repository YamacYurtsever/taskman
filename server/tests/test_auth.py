import os
import unittest
from unittest.mock import MagicMock, patch

from server import create_app
from server.config import DEFAULTS
from server.constants import FRONTEND_URL
from server.tests.utils import TEST_CONFIG, make_db, saved_config


class AuthStatusTest(unittest.TestCase):

    def setUp(self):
        self.app = create_app(TEST_CONFIG)
        self.client = self.app.test_client()

    def test_returns_false_when_not_authenticated(self):
        res = self.client.get("/api/auth/status")

        self.assertEqual(res.status_code, 200)
        self.assertFalse(res.get_json()["authenticated"])

    def test_returns_true_when_authenticated(self):
        with self.client.session_transaction() as sess:
            sess["authenticated"] = True
            sess["email"] = "user@gmail.com"

        res = self.client.get("/api/auth/status")

        self.assertEqual(res.status_code, 200)
        self.assertTrue(res.get_json()["authenticated"])


class RequireAuthTest(unittest.TestCase):

    def setUp(self):
        self.app = create_app(TEST_CONFIG)
        self.client = self.app.test_client()
        self.config_patcher = patch("server.config.load", return_value={"calendarTimezone": "UTC"})
        self.config_patcher.start()

    def tearDown(self):
        self.config_patcher.stop()

    def test_protected_route_rejects_unauthenticated(self):
        res = self.client.get("/api/state")

        self.assertEqual(res.status_code, 401)
        self.assertFalse(res.get_json()["ok"])

    def test_protected_route_allows_authenticated(self):
        with self.client.session_transaction() as sess:
            sess["authenticated"] = True
            sess["email"] = "user@gmail.com"

        with patch("server.db.load", return_value=make_db()):
            res = self.client.get("/api/state")

        self.assertEqual(res.status_code, 200)


class OAuthStartTest(unittest.TestCase):

    def setUp(self):
        self.app = create_app(TEST_CONFIG)
        self.client = self.app.test_client()

    def _mock_start_flow(self, state="state-abc"):
        mock_flow = MagicMock()
        mock_flow.code_verifier = None
        mock_flow.authorization_url.return_value = (
            "https://accounts.google.com/consent",
            state,
        )
        return mock_flow

    def test_returns_google_consent_url(self):
        with (
            patch.dict(os.environ, {
                "GOOGLE_CLIENT_ID": "cid",
                "GOOGLE_CLIENT_SECRET": "csec",
            }),
            patch("server.services.auth.Flow") as MockFlow,
        ):
            MockFlow.from_client_config.return_value = self._mock_start_flow()
            res = self.client.get("/api/oauth/start")

        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.get_json()["url"], "https://accounts.google.com/consent")

    def test_stores_state_in_session(self):
        with (
            patch.dict(os.environ, {
                "GOOGLE_CLIENT_ID": "cid",
                "GOOGLE_CLIENT_SECRET": "csec",
            }),
            patch("server.services.auth.Flow") as MockFlow,
        ):
            MockFlow.from_client_config.return_value = self._mock_start_flow(state="state-xyz")
            self.client.get("/api/oauth/start")

        with self.client.session_transaction() as sess:
            self.assertEqual(sess.get("oauth_state"), "state-xyz")

    def test_requests_offline_access_and_consent(self):
        mock_flow = self._mock_start_flow()

        with (
            patch.dict(os.environ, {
                "GOOGLE_CLIENT_ID": "cid",
                "GOOGLE_CLIENT_SECRET": "csec",
            }),
            patch("server.services.auth.Flow") as MockFlow,
        ):
            MockFlow.from_client_config.return_value = mock_flow
            self.client.get("/api/oauth/start")

        mock_flow.authorization_url.assert_called_once_with(
            access_type="offline",
            prompt="consent",
        )


class OAuthCallbackTest(unittest.TestCase):

    def setUp(self):
        self.app = create_app(TEST_CONFIG)
        self.client = self.app.test_client()

    def _mock_flow(self, refresh_token="reftok"):
        mock_creds = MagicMock()
        mock_creds.refresh_token = refresh_token

        mock_flow = MagicMock()
        mock_flow.credentials = mock_creds
        return mock_flow

    def _mock_userinfo_service(self, email="user@gmail.com"):
        mock_svc = MagicMock()
        mock_svc.userinfo().get().execute.return_value = {"email": email}
        return mock_svc

    def test_rejects_missing_state(self):
        res = self.client.get("/api/oauth/callback?code=authcode&state=state-abc")

        self.assertEqual(res.status_code, 400)
        self.assertFalse(res.get_json()["ok"])

    def test_rejects_invalid_state(self):
        with self.client.session_transaction() as sess:
            sess["oauth_state"] = "state-abc"

        res = self.client.get("/api/oauth/callback?code=authcode&state=wrong")

        self.assertEqual(res.status_code, 400)
        self.assertFalse(res.get_json()["ok"])

    def test_fetches_token_using_authorization_response(self):
        with self.client.session_transaction() as sess:
            sess["oauth_state"] = "state-abc"

        mock_flow = self._mock_flow()

        with saved_config({**DEFAULTS}):
            with (
                patch.dict(os.environ, {
                    "GOOGLE_CLIENT_ID": "cid",
                    "GOOGLE_CLIENT_SECRET": "csec",
                }),
                patch("server.db.load", return_value=make_db()),
                patch("server.services.auth.Flow") as MockFlow,
                patch("server.services.auth.build", return_value=self._mock_userinfo_service()),
            ):
                MockFlow.from_client_config.return_value = mock_flow
                self.client.get("/api/oauth/callback?code=authcode&state=state-abc")

        mock_flow.fetch_token.assert_called_once()
        kwargs = mock_flow.fetch_token.call_args.kwargs
        self.assertIn("authorization_response", kwargs)
        self.assertIn("code=authcode", kwargs["authorization_response"])

    def test_rejects_missing_refresh_token(self):
        with self.client.session_transaction() as sess:
            sess["oauth_state"] = "state-abc"

        with saved_config({**DEFAULTS}):
            with (
                patch.dict(os.environ, {
                    "GOOGLE_CLIENT_ID": "cid",
                    "GOOGLE_CLIENT_SECRET": "csec",
                }),
                patch("server.db.load", return_value=make_db()),
                patch("server.services.auth.Flow") as MockFlow,
            ):
                MockFlow.from_client_config.return_value = self._mock_flow(refresh_token=None)
                res = self.client.get("/api/oauth/callback?code=authcode&state=state-abc")

        self.assertEqual(res.status_code, 400)
        self.assertFalse(res.get_json()["ok"])

    def test_stores_refresh_token_and_email(self):
        with self.client.session_transaction() as sess:
            sess["oauth_state"] = "state-abc"

        with saved_config({**DEFAULTS}) as saved:
            with (
                patch.dict(os.environ, {
                    "GOOGLE_CLIENT_ID": "cid",
                    "GOOGLE_CLIENT_SECRET": "csec",
                }),
                patch("server.db.load", return_value=make_db()),
                patch("server.services.auth.Flow") as MockFlow,
                patch("server.services.auth.build", return_value=self._mock_userinfo_service()),
            ):
                MockFlow.from_client_config.return_value = self._mock_flow()
                self.client.get("/api/oauth/callback?code=authcode&state=state-abc")

        self.assertEqual(saved.get("googleRefreshToken"), "reftok")
        self.assertEqual(saved.get("googleEmail"), "user@gmail.com")

    def test_redirects_to_frontend(self):
        with self.client.session_transaction() as sess:
            sess["oauth_state"] = "state-abc"
            sess["frontend_url"] = FRONTEND_URL

        with saved_config({**DEFAULTS}):
            with (
                patch.dict(os.environ, {
                    "GOOGLE_CLIENT_ID": "cid",
                    "GOOGLE_CLIENT_SECRET": "csec",
                }),
                patch("server.db.load", return_value=make_db()),
                patch("server.services.auth.Flow") as MockFlow,
                patch("server.services.auth.build", return_value=self._mock_userinfo_service()),
            ):
                MockFlow.from_client_config.return_value = self._mock_flow()
                res = self.client.get("/api/oauth/callback?code=authcode&state=state-abc")

        self.assertEqual(res.status_code, 302)
        self.assertEqual(res.headers["Location"], FRONTEND_URL)

    def test_sets_authenticated_in_session(self):
        with self.client.session_transaction() as sess:
            sess["oauth_state"] = "state-abc"

        with saved_config({**DEFAULTS}):
            with (
                patch.dict(os.environ, {
                    "GOOGLE_CLIENT_ID": "cid",
                    "GOOGLE_CLIENT_SECRET": "csec",
                }),
                patch("server.db.load", return_value=make_db()),
                patch("server.services.auth.Flow") as MockFlow,
                patch("server.services.auth.build", return_value=self._mock_userinfo_service()),
            ):
                MockFlow.from_client_config.return_value = self._mock_flow()
                self.client.get("/api/oauth/callback?code=authcode&state=state-abc")

        res = self.client.get("/api/auth/status")

        self.assertTrue(res.get_json()["authenticated"])

        with self.client.session_transaction() as sess:
            self.assertEqual(sess.get("email"), "user@gmail.com")


class LogoutTest(unittest.TestCase):

    def setUp(self):
        self.app = create_app(TEST_CONFIG)
        self.client = self.app.test_client()

    def test_logout_clears_session(self):
        with self.client.session_transaction() as sess:
            sess["authenticated"] = True

        res = self.client.post("/api/logout")

        self.assertEqual(res.status_code, 200)

        status = self.client.get("/api/auth/status")
        self.assertFalse(status.get_json()["authenticated"])


class ConfigCalendarFetchTest(unittest.TestCase):

    def setUp(self):
        self.app = create_app(TEST_CONFIG)
        self.client = self.app.test_client()

        with self.client.session_transaction() as sess:
            sess["authenticated"] = True
            sess["email"] = "user@gmail.com"

    def test_fetches_user_calendars_when_refresh_token_present(self):
        cfg = {**DEFAULTS, "googleRefreshToken": "reftok"}

        mock_svc = MagicMock()
        mock_svc.calendarList().list().execute.return_value = {
            "items": [{"id": "a@gmail.com", "summary": "Personal"}],
        }

        with (
            patch.dict(os.environ, {
                "GOOGLE_CLIENT_ID": "cid",
                "GOOGLE_CLIENT_SECRET": "csec",
            }),
            patch("server.config.load", return_value=cfg),
            patch("server.services.auth.Credentials") as MockCredentials,
            patch("server.services.auth.build", return_value=mock_svc),
        ):
            res = self.client.get("/api/config")

        self.assertEqual(res.status_code, 200)

        MockCredentials.assert_called_once()
        kwargs = MockCredentials.call_args.kwargs
        self.assertEqual(kwargs["refresh_token"], "reftok")
        self.assertEqual(kwargs["client_id"], "cid")
        self.assertEqual(kwargs["client_secret"], "csec")

        user_cals = res.get_json()["userCalendars"]
        self.assertEqual(len(user_cals), 1)
        self.assertEqual(user_cals[0]["id"], "a@gmail.com")
        self.assertEqual(user_cals[0]["summary"], "Personal")

    def test_returns_empty_user_calendars_without_refresh_token(self):
        with patch("server.config.load", return_value={**DEFAULTS}):
            res = self.client.get("/api/config")

        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.get_json()["userCalendars"], [])

    def test_returns_empty_user_calendars_on_api_error(self):
        cfg = {**DEFAULTS, "googleRefreshToken": "reftok"}

        mock_svc = MagicMock()
        mock_svc.calendarList().list().execute.side_effect = Exception("API error")

        with (
            patch.dict(os.environ, {
                "GOOGLE_CLIENT_ID": "cid",
                "GOOGLE_CLIENT_SECRET": "csec",
            }),
            patch("server.config.load", return_value=cfg),
            patch("server.services.auth.Credentials"),
            patch("server.services.auth.build", return_value=mock_svc),
        ):
            res = self.client.get("/api/config")

        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.get_json()["userCalendars"], [])


class OAuthUrlGenerationTest(unittest.TestCase):

    def test_redirect_uri_uses_taskman_base_url(self):
        from server.services.auth import _redirect_uri
        with patch.dict(os.environ, {"TASKMAN_BASE_URL": "https://taskman.example.com"}):
            self.assertEqual(_redirect_uri(), "https://taskman.example.com/api/oauth/callback")

    def test_redirect_uri_falls_back_to_dev(self):
        from server.services.auth import _redirect_uri
        env = {k: v for k, v in os.environ.items() if k != "TASKMAN_BASE_URL"}
        with patch.dict(os.environ, env, clear=True):
            self.assertIn("127.0.0.1:5050", _redirect_uri())

    def test_redirect_uri_strips_trailing_slash(self):
        from server.services.auth import _redirect_uri
        with patch.dict(os.environ, {"TASKMAN_BASE_URL": "https://taskman.example.com/"}):
            self.assertEqual(_redirect_uri(), "https://taskman.example.com/api/oauth/callback")

    def test_frontend_url_uses_taskman_base_url_regardless_of_origin(self):
        from server.services.auth import _frontend_url
        with patch.dict(os.environ, {"TASKMAN_BASE_URL": "https://taskman.example.com"}):
            self.assertEqual(_frontend_url("http://some-origin.com"), "https://taskman.example.com")

    def test_frontend_url_uses_origin_in_dev(self):
        from server.services.auth import _frontend_url
        env = {k: v for k, v in os.environ.items() if k != "TASKMAN_BASE_URL"}
        with patch.dict(os.environ, env, clear=True):
            self.assertEqual(_frontend_url("http://127.0.0.1:5173"), "http://127.0.0.1:5173")

    def test_frontend_url_falls_back_to_constant_when_no_origin_in_dev(self):
        from server.services.auth import _frontend_url
        env = {k: v for k, v in os.environ.items() if k != "TASKMAN_BASE_URL"}
        with patch.dict(os.environ, env, clear=True):
            self.assertEqual(_frontend_url(None), FRONTEND_URL)


class ProductionConfigTest(unittest.TestCase):

    def test_production_session_cookie_secure_is_true(self):
        with patch.dict(os.environ, {
            "TASKMAN_BASE_URL": "https://taskman.example.com",
            "GOOGLE_CLIENT_ID": "cid",
            "GOOGLE_CLIENT_SECRET": "csec",
        }):
            with patch("server.config.load", return_value={"secretKey": "s"}), \
                 patch("server.config.save"), \
                 patch("pathlib.Path.mkdir"):
                app = create_app()
        self.assertTrue(app.config.get("SESSION_COOKIE_SECURE"))

    def test_dev_session_cookie_secure_is_false(self):
        env = {k: v for k, v in os.environ.items() if k != "TASKMAN_BASE_URL"}
        with patch.dict(os.environ, env, clear=True):
            with patch("server.config.load", return_value={"secretKey": "s"}), \
                 patch("server.config.save"), \
                 patch("pathlib.Path.mkdir"):
                app = create_app()
        self.assertFalse(app.config.get("SESSION_COOKIE_SECURE"))

    def test_production_raises_on_missing_oauth_env_vars(self):
        env = {k: v for k, v in os.environ.items()
               if k not in ("GOOGLE_CLIENT_ID", "GOOGLE_CLIENT_SECRET")}
        env["TASKMAN_BASE_URL"] = "https://taskman.example.com"
        with patch.dict(os.environ, env, clear=True):
            with self.assertRaises(RuntimeError) as ctx:
                create_app()
        self.assertIn("GOOGLE_CLIENT_ID", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
