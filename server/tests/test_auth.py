import os
import unittest
from unittest.mock import MagicMock, patch

from google.auth.exceptions import RefreshError
from oauthlib.oauth2.rfc6749.errors import AccessDeniedError

from server import create_app
from server.config import DEFAULTS
from server.constants import FRONTEND_URL
from server.tests.utils import TEST_CONFIG, TODAY, make_db, saved_config


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

    def test_handles_user_denying_consent(self):
        with self.client.session_transaction() as sess:
            sess["oauth_state"] = "state-abc"

        mock_flow = self._mock_flow()
        mock_flow.fetch_token.side_effect = AccessDeniedError()

        with (
            patch.dict(os.environ, {
                "GOOGLE_CLIENT_ID": "cid",
                "GOOGLE_CLIENT_SECRET": "csec",
            }),
            patch("server.services.auth.Flow") as MockFlow,
        ):
            MockFlow.from_client_config.return_value = mock_flow
            res = self.client.get(
                "/api/oauth/callback?error=access_denied&state=state-abc"
            )

        self.assertEqual(res.status_code, 400)
        self.assertFalse(res.get_json()["ok"])

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

    def test_reconnect_allows_same_account(self):
        with self.client.session_transaction() as sess:
            sess["oauth_state"] = "state-abc"
            sess["authenticated"] = True
            sess["email"] = "user@gmail.com"

        with saved_config({**DEFAULTS}):
            with (
                patch.dict(os.environ, {
                    "GOOGLE_CLIENT_ID": "cid",
                    "GOOGLE_CLIENT_SECRET": "csec",
                }),
                patch("server.db.load", return_value=make_db()),
                patch("server.services.auth.Flow") as MockFlow,
                patch("server.services.auth.build", return_value=self._mock_userinfo_service(email="user@gmail.com")),
            ):
                MockFlow.from_client_config.return_value = self._mock_flow()
                res = self.client.get("/api/oauth/callback?code=authcode&state=state-abc")

        self.assertEqual(res.status_code, 302)

    def test_reconnect_rejects_mismatched_account(self):
        with self.client.session_transaction() as sess:
            sess["oauth_state"] = "state-abc"
            sess["authenticated"] = True
            sess["email"] = "user@gmail.com"

        with saved_config({**DEFAULTS}):
            with (
                patch.dict(os.environ, {
                    "GOOGLE_CLIENT_ID": "cid",
                    "GOOGLE_CLIENT_SECRET": "csec",
                }),
                patch("server.db.load", return_value=make_db()),
                patch("server.services.auth.Flow") as MockFlow,
                patch("server.services.auth.build", return_value=self._mock_userinfo_service(email="other@gmail.com")),
            ):
                MockFlow.from_client_config.return_value = self._mock_flow()
                res = self.client.get("/api/oauth/callback?code=authcode&state=state-abc")

        self.assertEqual(res.status_code, 400)
        self.assertFalse(res.get_json()["ok"])

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

    def test_calendar_auth_valid_true_when_calendars_fetch_succeeds(self):
        cfg = {**DEFAULTS, "googleRefreshToken": "reftok"}

        mock_svc = MagicMock()
        mock_svc.calendarList().list().execute.return_value = {"items": []}

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

        self.assertTrue(res.get_json()["calendarAuthValid"])

    def test_calendar_auth_invalid_when_refresh_token_revoked(self):
        cfg = {**DEFAULTS, "googleRefreshToken": "reftok"}

        mock_svc = MagicMock()
        mock_svc.calendarList().list().execute.side_effect = RefreshError("invalid_grant")

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
        self.assertFalse(res.get_json()["calendarAuthValid"])
        self.assertEqual(res.get_json()["userCalendars"], [])
        self.assertEqual(res.get_json()["calendarUrl"], "")

    def test_calendar_auth_valid_true_without_refresh_token(self):
        with patch("server.config.load", return_value={**DEFAULTS}):
            res = self.client.get("/api/config")

        self.assertTrue(res.get_json()["calendarAuthValid"])


class NextEventTest(unittest.TestCase):

    def setUp(self):
        self.app = create_app(TEST_CONFIG)
        self.client = self.app.test_client()

        with self.client.session_transaction() as sess:
            sess["authenticated"] = True
            sess["email"] = "user@gmail.com"

        self.today_patcher = patch("server.services.auth.today_in_timezone", return_value=TODAY)
        self.today_patcher.start()

    def tearDown(self):
        self.today_patcher.stop()

    def _mock_svc(self, calendars=None, **event_kwargs):
        mock_svc = MagicMock()
        mock_svc.calendarList().list().execute.return_value = {"items": calendars or []}
        if event_kwargs.get("side_effect") is not None:
            mock_svc.events().list().execute.side_effect = event_kwargs["side_effect"]
        else:
            mock_svc.events().list().execute.return_value = event_kwargs.get("return_value", {"items": []})
        return mock_svc

    def test_returns_none_without_refresh_token(self):
        with patch("server.config.load", return_value={**DEFAULTS}):
            res = self.client.get("/api/next-event")

        self.assertEqual(res.status_code, 200)
        self.assertIsNone(res.get_json()["event"])

    def test_returns_next_timed_event(self):
        cfg = {**DEFAULTS, "googleRefreshToken": "reftok", "calendars": [{"id": "cal-1"}]}
        mock_svc = self._mock_svc(return_value={
            "items": [{
                "summary": "Standup",
                "start": {"dateTime": "2026-04-27T15:00:00+10:00"},
                "end": {"dateTime": "2026-04-27T15:30:00+10:00"},
            }],
        })

        with (
            patch.dict(os.environ, {"GOOGLE_CLIENT_ID": "cid", "GOOGLE_CLIENT_SECRET": "csec"}),
            patch("server.config.load", return_value=cfg),
            patch("server.services.auth.Credentials"),
            patch("server.services.auth.build", return_value=mock_svc),
        ):
            res = self.client.get("/api/next-event")

        event = res.get_json()["event"]
        self.assertEqual(event["title"], "Standup")
        self.assertEqual(event["startTime"], "05.00")
        self.assertEqual(event["endTime"], "05.30")
        self.assertIsNotNone(event["startIso"])
        self.assertIsNotNone(event["endIso"])
        self.assertFalse(event["hasOverlap"])
        self.assertEqual(event["date"], "2026-04-27")
        self.assertEqual(event["dayLabel"], "Tmr")

    def test_day_label_is_none_for_today(self):
        cfg = {**DEFAULTS, "googleRefreshToken": "reftok", "calendars": [{"id": "cal-1"}]}
        mock_svc = self._mock_svc(return_value={
            "items": [{
                "summary": "Standup",
                "start": {"dateTime": f"{TODAY}T15:00:00Z"},
                "end": {"dateTime": f"{TODAY}T15:30:00Z"},
            }],
        })

        with (
            patch.dict(os.environ, {"GOOGLE_CLIENT_ID": "cid", "GOOGLE_CLIENT_SECRET": "csec"}),
            patch("server.config.load", return_value=cfg),
            patch("server.services.auth.Credentials"),
            patch("server.services.auth.build", return_value=mock_svc),
        ):
            res = self.client.get("/api/next-event")

        self.assertIsNone(res.get_json()["event"]["dayLabel"])

    def test_day_label_is_tmr_for_tomorrow(self):
        cfg = {**DEFAULTS, "googleRefreshToken": "reftok", "calendars": [{"id": "cal-1"}]}
        mock_svc = self._mock_svc(return_value={
            "items": [{
                "summary": "Standup",
                "start": {"dateTime": "2026-04-27T15:00:00Z"},
                "end": {"dateTime": "2026-04-27T15:30:00Z"},
            }],
        })

        with (
            patch.dict(os.environ, {"GOOGLE_CLIENT_ID": "cid", "GOOGLE_CLIENT_SECRET": "csec"}),
            patch("server.config.load", return_value=cfg),
            patch("server.services.auth.Credentials"),
            patch("server.services.auth.build", return_value=mock_svc),
        ):
            res = self.client.get("/api/next-event")

        self.assertEqual(res.get_json()["event"]["dayLabel"], "Tmr")

    def test_day_label_is_weekday_within_this_week(self):
        # TODAY is 2026-04-26 (a Sunday); 3 days out is 2026-04-29 (Wednesday).
        cfg = {**DEFAULTS, "googleRefreshToken": "reftok", "calendars": [{"id": "cal-1"}]}
        mock_svc = self._mock_svc(return_value={
            "items": [{
                "summary": "Standup",
                "start": {"dateTime": "2026-04-29T15:00:00Z"},
                "end": {"dateTime": "2026-04-29T15:30:00Z"},
            }],
        })

        with (
            patch.dict(os.environ, {"GOOGLE_CLIENT_ID": "cid", "GOOGLE_CLIENT_SECRET": "csec"}),
            patch("server.config.load", return_value=cfg),
            patch("server.services.auth.Credentials"),
            patch("server.services.auth.build", return_value=mock_svc),
        ):
            res = self.client.get("/api/next-event")

        self.assertEqual(res.get_json()["event"]["dayLabel"], "Wed")

    def test_filters_out_events_more_than_a_week_away(self):
        cfg = {**DEFAULTS, "googleRefreshToken": "reftok", "calendars": [{"id": "cal-1"}]}
        mock_svc = self._mock_svc(return_value={
            "items": [{
                "summary": "Standup",
                "start": {"dateTime": "2026-05-18T15:00:00Z"},
                "end": {"dateTime": "2026-05-18T15:30:00Z"},
            }],
        })

        with (
            patch.dict(os.environ, {"GOOGLE_CLIENT_ID": "cid", "GOOGLE_CLIENT_SECRET": "csec"}),
            patch("server.config.load", return_value=cfg),
            patch("server.services.auth.Credentials"),
            patch("server.services.auth.build", return_value=mock_svc),
        ):
            res = self.client.get("/api/next-event")

        self.assertIsNone(res.get_json()["event"])

    def test_surfaces_within_week_event_even_when_a_farther_one_sorts_first_in_feed(self):
        cfg = {**DEFAULTS, "googleRefreshToken": "reftok", "calendars": [{"id": "cal-1"}]}
        mock_svc = self._mock_svc(return_value={
            "items": [
                {
                    "summary": "TooFarOut",
                    "start": {"dateTime": "2026-05-18T15:00:00Z"},
                    "end": {"dateTime": "2026-05-18T15:30:00Z"},
                },
                {
                    "summary": "WithinWeek",
                    "start": {"dateTime": "2026-04-29T15:00:00Z"},
                    "end": {"dateTime": "2026-04-29T15:30:00Z"},
                },
            ],
        })

        with (
            patch.dict(os.environ, {"GOOGLE_CLIENT_ID": "cid", "GOOGLE_CLIENT_SECRET": "csec"}),
            patch("server.config.load", return_value=cfg),
            patch("server.services.auth.Credentials"),
            patch("server.services.auth.build", return_value=mock_svc),
        ):
            res = self.client.get("/api/next-event")

        event = res.get_json()["event"]
        self.assertEqual(event["title"], "WithinWeek")
        self.assertEqual(event["dayLabel"], "Wed")

    def test_returns_none_when_no_upcoming_events(self):
        cfg = {**DEFAULTS, "googleRefreshToken": "reftok", "calendars": [{"id": "cal-1"}]}
        mock_svc = self._mock_svc()

        with (
            patch.dict(os.environ, {"GOOGLE_CLIENT_ID": "cid", "GOOGLE_CLIENT_SECRET": "csec"}),
            patch("server.config.load", return_value=cfg),
            patch("server.services.auth.Credentials"),
            patch("server.services.auth.build", return_value=mock_svc),
        ):
            res = self.client.get("/api/next-event")

        self.assertIsNone(res.get_json()["event"])

    def test_picks_earliest_across_multiple_calendars(self):
        cfg = {**DEFAULTS, "googleRefreshToken": "reftok", "calendars": [{"id": "cal-1"}, {"id": "cal-2"}]}
        mock_svc = self._mock_svc(side_effect=[
            {"items": [{
                "summary": "Later",
                "start": {"dateTime": "2026-04-27T18:00:00+10:00"},
                "end": {"dateTime": "2026-04-27T18:30:00+10:00"},
            }]},
            {"items": [{
                "summary": "Sooner",
                "start": {"dateTime": "2026-04-27T14:00:00+10:00"},
                "end": {"dateTime": "2026-04-27T14:30:00+10:00"},
            }]},
        ])

        with (
            patch.dict(os.environ, {"GOOGLE_CLIENT_ID": "cid", "GOOGLE_CLIENT_SECRET": "csec"}),
            patch("server.config.load", return_value=cfg),
            patch("server.services.auth.Credentials"),
            patch("server.services.auth.build", return_value=mock_svc),
        ):
            res = self.client.get("/api/next-event")

        self.assertEqual(res.get_json()["event"]["title"], "Sooner")

    def test_detects_overlap_within_same_calendar(self):
        cfg = {**DEFAULTS, "googleRefreshToken": "reftok", "calendars": [{"id": "cal-1"}]}
        mock_svc = self._mock_svc(return_value={
            "items": [
                {
                    "summary": "Standup",
                    "start": {"dateTime": "2026-04-27T15:00:00+10:00"},
                    "end": {"dateTime": "2026-04-27T15:30:00+10:00"},
                },
                {
                    "summary": "Overlapping",
                    "start": {"dateTime": "2026-04-27T15:15:00+10:00"},
                    "end": {"dateTime": "2026-04-27T16:00:00+10:00"},
                },
            ],
        })

        with (
            patch.dict(os.environ, {"GOOGLE_CLIENT_ID": "cid", "GOOGLE_CLIENT_SECRET": "csec"}),
            patch("server.config.load", return_value=cfg),
            patch("server.services.auth.Credentials"),
            patch("server.services.auth.build", return_value=mock_svc),
        ):
            res = self.client.get("/api/next-event")

        event = res.get_json()["event"]
        self.assertEqual(event["title"], "Standup")
        self.assertTrue(event["hasOverlap"])

    def test_detects_overlap_across_calendars(self):
        cfg = {**DEFAULTS, "googleRefreshToken": "reftok", "calendars": [{"id": "cal-1"}, {"id": "cal-2"}]}
        mock_svc = self._mock_svc(side_effect=[
            {"items": [{
                "summary": "Standup",
                "start": {"dateTime": "2026-04-27T15:00:00+10:00"},
                "end": {"dateTime": "2026-04-27T15:30:00+10:00"},
            }]},
            {"items": [{
                "summary": "Overlapping",
                "start": {"dateTime": "2026-04-27T15:15:00+10:00"},
                "end": {"dateTime": "2026-04-27T16:00:00+10:00"},
            }]},
        ])

        with (
            patch.dict(os.environ, {"GOOGLE_CLIENT_ID": "cid", "GOOGLE_CLIENT_SECRET": "csec"}),
            patch("server.config.load", return_value=cfg),
            patch("server.services.auth.Credentials"),
            patch("server.services.auth.build", return_value=mock_svc),
        ):
            res = self.client.get("/api/next-event")

        event = res.get_json()["event"]
        self.assertEqual(event["title"], "Standup")
        self.assertTrue(event["hasOverlap"])

    def test_no_overlap_when_next_event_starts_after_current_one_ends(self):
        cfg = {**DEFAULTS, "googleRefreshToken": "reftok", "calendars": [{"id": "cal-1"}]}
        mock_svc = self._mock_svc(return_value={
            "items": [
                {
                    "summary": "Standup",
                    "start": {"dateTime": "2026-04-27T15:00:00+10:00"},
                    "end": {"dateTime": "2026-04-27T15:30:00+10:00"},
                },
                {
                    "summary": "Later",
                    "start": {"dateTime": "2026-04-27T16:00:00+10:00"},
                    "end": {"dateTime": "2026-04-27T16:30:00+10:00"},
                },
            ],
        })

        with (
            patch.dict(os.environ, {"GOOGLE_CLIENT_ID": "cid", "GOOGLE_CLIENT_SECRET": "csec"}),
            patch("server.config.load", return_value=cfg),
            patch("server.services.auth.Credentials"),
            patch("server.services.auth.build", return_value=mock_svc),
        ):
            res = self.client.get("/api/next-event")

        self.assertFalse(res.get_json()["event"]["hasOverlap"])

    def test_ignores_all_day_events_entirely(self):
        cfg = {**DEFAULTS, "googleRefreshToken": "reftok", "calendars": [{"id": "cal-1"}]}
        mock_svc = self._mock_svc(return_value={
            "items": [{"summary": "Holiday", "start": {"date": "2026-08-01"}}],
        })

        with (
            patch.dict(os.environ, {"GOOGLE_CLIENT_ID": "cid", "GOOGLE_CLIENT_SECRET": "csec"}),
            patch("server.config.load", return_value=cfg),
            patch("server.services.auth.Credentials"),
            patch("server.services.auth.build", return_value=mock_svc),
        ):
            res = self.client.get("/api/next-event")

        self.assertIsNone(res.get_json()["event"])

    def test_skips_leading_all_day_events_to_find_next_timed_event(self):
        cfg = {**DEFAULTS, "googleRefreshToken": "reftok", "calendars": [{"id": "cal-1"}]}
        mock_svc = self._mock_svc(return_value={
            "items": [
                {"summary": "Holiday", "start": {"date": "2026-04-27"}},
                {
                    "summary": "Standup",
                    "start": {"dateTime": "2026-04-27T15:00:00+10:00"},
                    "end": {"dateTime": "2026-04-27T15:30:00+10:00"},
                },
            ],
        })

        with (
            patch.dict(os.environ, {"GOOGLE_CLIENT_ID": "cid", "GOOGLE_CLIENT_SECRET": "csec"}),
            patch("server.config.load", return_value=cfg),
            patch("server.services.auth.Credentials"),
            patch("server.services.auth.build", return_value=mock_svc),
        ):
            res = self.client.get("/api/next-event")

        event = res.get_json()["event"]
        self.assertEqual(event["title"], "Standup")

    def test_returns_none_on_revoked_refresh_token(self):
        cfg = {**DEFAULTS, "googleRefreshToken": "reftok", "calendars": [{"id": "cal-1"}]}
        mock_svc = self._mock_svc()
        mock_svc.events().list().execute.side_effect = RefreshError("invalid_grant")

        with (
            patch.dict(os.environ, {"GOOGLE_CLIENT_ID": "cid", "GOOGLE_CLIENT_SECRET": "csec"}),
            patch("server.config.load", return_value=cfg),
            patch("server.services.auth.Credentials"),
            patch("server.services.auth.build", return_value=mock_svc),
        ):
            res = self.client.get("/api/next-event")

        self.assertEqual(res.status_code, 200)
        self.assertIsNone(res.get_json()["event"])

    def test_falls_back_to_user_calendars_when_none_configured(self):
        cfg = {**DEFAULTS, "googleRefreshToken": "reftok"}
        mock_svc = self._mock_svc(
            calendars=[{"id": "a@gmail.com", "summary": "Personal"}],
            return_value={"items": [{
                "summary": "Dentist",
                "start": {"dateTime": "2026-04-27T09:00:00+10:00"},
                "end": {"dateTime": "2026-04-27T09:30:00+10:00"},
            }]},
        )

        with (
            patch.dict(os.environ, {"GOOGLE_CLIENT_ID": "cid", "GOOGLE_CLIENT_SECRET": "csec"}),
            patch("server.config.load", return_value=cfg),
            patch("server.services.auth.Credentials"),
            patch("server.services.auth.build", return_value=mock_svc),
        ):
            res = self.client.get("/api/next-event")

        self.assertEqual(res.get_json()["event"]["title"], "Dentist")


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
