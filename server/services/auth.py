import os

from google.auth.exceptions import RefreshError
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from oauthlib.oauth2.rfc6749.errors import OAuth2Error

from server import config, db
from server.constants import CALENDAR_PRESET_COLORS, DEV_API_BASE, FRONTEND_URL
from server.services.utils import (
    UTC_DATETIME_FORMAT,
    ServiceError,
    local_datetime_from_storage,
    parse_utc_datetime,
    utc_now,
)

# oauthlib raises a bare Warning (not caught by `except OAuth2Error`) when the
# granted scope differs from the requested one — e.g. the user declines the
# calendar scope while still approving sign-in. This makes that non-fatal.
os.environ.setdefault("OAUTHLIB_RELAX_TOKEN_SCOPE", "1")


class CalendarAuthError(Exception):
    """Raised when the stored Google refresh token is invalid/revoked."""

SCOPES = [
    "openid",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/calendar.readonly",
]


def _redirect_uri() -> str:
    base = os.environ.get("TASKMAN_BASE_URL", DEV_API_BASE)
    return base.rstrip("/") + "/api/oauth/callback"


def _frontend_url(origin: str | None) -> str:
    base = os.environ.get("TASKMAN_BASE_URL")
    if base:
        return base.rstrip("/")
    return origin or FRONTEND_URL


def default_frontend_url() -> str:
    return _frontend_url(None)


def is_authenticated(session_data) -> bool:
    return bool(session_data.get("authenticated") and session_data.get("email"))


def google_client_config() -> dict:
    client_id = os.environ.get("GOOGLE_CLIENT_ID")
    client_secret = os.environ.get("GOOGLE_CLIENT_SECRET")

    if not client_id or not client_secret:
        raise ServiceError("Google OAuth is not configured")

    return {"web": {
        "client_id": client_id,
        "client_secret": client_secret,
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "redirect_uris": [_redirect_uri()],
    }}


def begin_oauth(origin: str | None) -> dict:
    redirect = _redirect_uri()
    flow = Flow.from_client_config(google_client_config(), scopes=SCOPES)
    flow.redirect_uri = redirect

    url, state = flow.authorization_url(
        access_type="offline",
        prompt="consent",
    )

    return {
        "url": url,
        "state": state,
        "code_verifier": flow.code_verifier,
        "frontend_url": _frontend_url(origin),
    }


def complete_oauth(request_url: str, expected_state: str | None, received_state: str | None, code_verifier: str | None) -> dict:
    if not expected_state or received_state != expected_state:
        raise ServiceError("invalid oauth state")

    flow = Flow.from_client_config(
        google_client_config(),
        scopes=SCOPES,
        state=expected_state,
        code_verifier=code_verifier,
    )
    flow.redirect_uri = _redirect_uri()
    try:
        flow.fetch_token(authorization_response=request_url)
    except OAuth2Error as e:
        raise ServiceError("Google sign-in was cancelled or denied") from e

    credentials = flow.credentials
    if not credentials.refresh_token:
        raise ServiceError("missing refresh token")

    try:
        svc = build("oauth2", "v2", credentials=credentials)
        user_info = svc.userinfo().get().execute()
        email = user_info.get("email")
    except Exception as e:
        raise ServiceError(f"failed to fetch Google email: {e}") from e

    if not email:
        raise ServiceError("missing Google email")

    return {
        "email": email,
        "refresh_token": credentials.refresh_token,
    }


def persist_user_auth(email: str, refresh_token: str) -> None:
    shared_only_cfg = config.load()
    user_cfg = config.load(email)
    user_cfg["googleRefreshToken"] = refresh_token
    user_cfg["googleEmail"] = email

    config.save(shared_only_cfg)
    config.save(user_cfg, email)
    db.load(email)


def _credentials(refresh_token: str) -> Credentials:
    return Credentials(
        token=None,
        refresh_token=refresh_token,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=os.environ.get("GOOGLE_CLIENT_ID", ""),
        client_secret=os.environ.get("GOOGLE_CLIENT_SECRET", ""),
    )


def fetch_user_calendars(refresh_token: str | None) -> list[dict]:
    if not refresh_token:
        return []

    try:
        svc = build("calendar", "v3", credentials=_credentials(refresh_token))
        result = svc.calendarList().list().execute()
        return [
            {"id": c["id"], "summary": c.get("summary", "")}
            for c in result.get("items", [])
        ]
    except RefreshError as e:
        raise CalendarAuthError from e
    except Exception:
        return []


def effective_calendar_ids(calendars: list, user_calendars: list[dict]) -> list[str]:
    ids = [c["id"] if isinstance(c, dict) else c for c in calendars]
    if not ids and user_calendars:
        ids = [c["id"] for c in user_calendars[:5]]
    return ids


# Per-calendar lookahead when scanning for the next *timed* event — all-day
# events are skipped entirely, so a small buffer covers a calendar whose
# next couple of entries happen to be all-day (e.g. a holiday) before a
# real timed event shows up.
EVENTS_LOOKAHEAD = 10


def _local_12h_time(dt, tz_name: str) -> str:
    return local_datetime_from_storage(
        dt.strftime(UTC_DATETIME_FORMAT), tz_name,
    ).strftime("%I:%M %p").lstrip("0")


def fetch_next_event(refresh_token: str | None, calendar_ids: list[str], tz_name: str) -> dict | None:
    if not refresh_token or not calendar_ids:
        return None

    try:
        svc = build("calendar", "v3", credentials=_credentials(refresh_token))
        now = utc_now()

        candidates = []
        for calendar_id in calendar_ids:
            result = svc.events().list(
                calendarId=calendar_id,
                timeMin=now,
                maxResults=EVENTS_LOOKAHEAD,
                singleEvents=True,
                orderBy="startTime",
            ).execute()
            timed_event = next(
                (e for e in result.get("items", []) if "dateTime" in e["start"]),
                None,
            )
            if timed_event:
                candidates.append(timed_event)

        if not candidates:
            return None

        earliest = min(candidates, key=lambda e: parse_utc_datetime(e["start"]["dateTime"]))
        start_dt = parse_utc_datetime(earliest["start"]["dateTime"])
        end_dt = parse_utc_datetime(earliest["end"]["dateTime"])

        return {
            "title": earliest.get("summary") or "(No title)",
            "startIso": start_dt.strftime(UTC_DATETIME_FORMAT),
            "endIso": end_dt.strftime(UTC_DATETIME_FORMAT),
            "startTime": _local_12h_time(start_dt, tz_name),
            "endTime": _local_12h_time(end_dt, tz_name),
        }
    except RefreshError as e:
        raise CalendarAuthError from e
    except Exception:
        return None


def build_calendar_url(calendars, timezone: str, user_calendars: list[dict]) -> str:
    parts = []
    for calendar in calendars:
        if isinstance(calendar, dict):
            parts.append(f"src={calendar['id']}")
            if calendar.get("color"):
                parts.append(f"color={calendar['color'].replace('#', '%23')}")
        else:
            parts.append(f"src={calendar}")

    if not parts and user_calendars:
        for i, cal in enumerate(user_calendars[:5]):
            parts.append(f"src={cal['id']}")
            parts.append(f"color={CALENDAR_PRESET_COLORS[i].replace('#', '%23')}")

    if not parts:
        return ""

    return f"https://calendar.google.com/calendar/embed?{'&'.join(parts)}&ctz={timezone}&mode=WEEK"
