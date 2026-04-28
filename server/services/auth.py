import os

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build

from server import config, db
from server.constants import CALENDAR_PRESET_COLORS, FRONTEND_URL
from server.services.utils import ServiceError

SCOPES = [
    "openid",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/calendar.readonly",
]

_DEV_API_BASE = "http://127.0.0.1:5050"


def _redirect_uri() -> str:
    base = os.environ.get("TASKMAN_BASE_URL", _DEV_API_BASE)
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
    flow.fetch_token(authorization_response=request_url)

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


def fetch_user_calendars(refresh_token: str | None) -> list[dict]:
    if not refresh_token:
        return []

    try:
        creds = Credentials(
            token=None,
            refresh_token=refresh_token,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=os.environ.get("GOOGLE_CLIENT_ID", ""),
            client_secret=os.environ.get("GOOGLE_CLIENT_SECRET", ""),
        )
        svc = build("calendar", "v3", credentials=creds)
        result = svc.calendarList().list().execute()
        return [
            {"id": c["id"], "summary": c.get("summary", "")}
            for c in result.get("items", [])
        ]
    except Exception:
        return []


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
