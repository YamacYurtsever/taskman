from datetime import datetime, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from server import db
from server.constants import DATE_FORMAT, DATE_INPUT_FORMATS


# ─────────────────────────── Errors & Validation ───────────────────────────

class ServiceError(Exception):
    pass


def service(fn):
    def wrapper(*args, **kwargs):
        try:
            fn(*args, **kwargs)
            return True, ""
        except ServiceError as e:
            return False, str(e)

    return wrapper


def require_name(value, field="name"):
    value = (value or "").strip()
    if not value:
        raise ServiceError(f"{field} is required")
    return value


# ─────────────────────────── Date / Time ───────────────────────────

UTC_SUFFIX = "Z"
UTC_DATETIME_FORMAT = "%Y-%m-%dT%H:%M:%SZ"
def parse_date(s):
    for fmt in DATE_INPUT_FORMATS:
        try:
            return datetime.strptime(s, fmt).strftime(DATE_FORMAT)
        except ValueError:
            pass
    raise ServiceError(f"invalid date '{s}' — expected YYYY-MM-DD")


def require_timezone(tz_name: str) -> str:
    try:
        ZoneInfo(tz_name)
    except ZoneInfoNotFoundError as e:
        raise ServiceError(f"invalid timezone '{tz_name}'") from e
    return tz_name


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime(UTC_DATETIME_FORMAT)


def today_in_timezone(tz_name: str) -> str:
    tz = ZoneInfo(require_timezone(tz_name))
    return datetime.now(timezone.utc).astimezone(tz).date().isoformat()


def parse_utc_datetime(value: str) -> datetime:
    if value.endswith(UTC_SUFFIX):
        return datetime.strptime(value, UTC_DATETIME_FORMAT).replace(tzinfo=timezone.utc)

    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None:
        raise ServiceError(f"invalid UTC datetime '{value}'")
    return parsed.astimezone(timezone.utc)


def local_datetime_from_storage(value: str, tz_name: str) -> datetime:
    tz = ZoneInfo(require_timezone(tz_name))
    return parse_utc_datetime(value).astimezone(tz)


def local_date_from_storage(value: str, tz_name: str) -> str:
    return local_datetime_from_storage(value, tz_name).date().isoformat()


def local_time_from_storage(value: str, tz_name: str) -> str:
    return local_datetime_from_storage(value, tz_name).strftime("%H:%M")


def storage_datetime_for_local_date(value: str, tz_name: str) -> str:
    tz = ZoneInfo(require_timezone(tz_name))
    local_date = datetime.strptime(parse_date(value), DATE_FORMAT).date()
    local_datetime = datetime(
        local_date.year,
        local_date.month,
        local_date.day,
        23,
        59,
        tzinfo=tz,
    )
    return local_datetime.astimezone(timezone.utc).strftime(UTC_DATETIME_FORMAT)


# ─────────────────────────── Find Helpers ───────────────────────────

def find_list(data, name):
    return next((l for l in data["lists"] if l["name"] == name), None)


def find_group(data, name):
    return next((g for g in data["groups"] if g["name"] == name), None)


def find_task(data, list_id, name):
    return next(
        (t for t in data["tasks"] if t["listId"] == list_id and t["name"] == name),
        None,
    )


def find_daysheet_entry(data, list_id, entry_type, text, entry_day, tz_name):
    return next(
        (
            e for e in data["daysheet"]
            if e["listId"] == list_id
            and e["type"] == entry_type
            and e["text"] == text
            and local_date_from_storage(e["datetime"], tz_name) == entry_day
        ),
        None,
    )


def has_daysheet_entry(data, list_id, entry_type, text, entry_day, tz_name):
    return find_daysheet_entry(data, list_id, entry_type, text, entry_day, tz_name) is not None


# ─────────────────────────── Require Helpers ───────────────────────────

def require_list(data, name, message=None):
    lst = find_list(data, name)
    if not lst:
        raise ServiceError(message or f"list '{name}' not found")
    return lst


def require_task(data, lst, name):
    task = find_task(data, lst["id"], name)
    if not task:
        raise ServiceError(f"task '{name}' not found in '{lst['name']}'")
    return task


# ─────────────────────────── Creation Helpers ───────────────────────────

def get_or_create_list(data, name):
    lst = find_list(data, name)
    if not lst:
        lst = {"id": db.new_id(), "name": name, "groupId": None}
        data["lists"].append(lst)
    return lst


def get_or_create_group(data, name):
    group = find_group(data, name)
    if not group:
        group = {"id": db.new_id(), "name": name}
        data["groups"].append(group)
    return group


def add_daysheet_entry(data, list_id, entry_type, text, timestamp=None):
    data["daysheet"].append({
        "id": db.new_id(),
        "datetime": timestamp or utc_now(),
        "listId": list_id,
        "type": entry_type,
        "text": text,
    })


# ─────────────────────────── Deletion / Mutation Helpers ───────────────────────────


def delete_group(data, group):
    for lst in data["lists"]:
        if lst["groupId"] == group["id"]:
            lst["groupId"] = None

    data["groups"] = [g for g in data["groups"] if g["id"] != group["id"]]


def delete_list(data, lst):
    data["tasks"] = [t for t in data["tasks"] if t["listId"] != lst["id"]]
    data["daysheet"] = [e for e in data["daysheet"] if e["listId"] != lst["id"]]
    data["lists"] = [l for l in data["lists"] if l["id"] != lst["id"]]


def remove_daysheet_entries(data, list_id, entry_type, tz_name, text=None, entry_day=None):
    before = len(data["daysheet"])

    data["daysheet"] = [
        e for e in data["daysheet"]
        if not (
            e["listId"] == list_id
            and e["type"] == entry_type
            and (text is None or e["text"] == text)
            and (entry_day is None or local_date_from_storage(e["datetime"], tz_name) == entry_day)
        )
    ]

    return before - len(data["daysheet"])
