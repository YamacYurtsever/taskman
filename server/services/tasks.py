import re

from server import db
from server.constants import DaysheetEntryType
from server.services.utils import (
    ServiceError,
    add_daysheet_entry,
    add_days_to_date,
    parse_date,
    remove_daysheet_entries,
    require_list,
    require_name,
    require_task_by_id,
    service,
    today_in_timezone,
    utc_now,
)

MAX_SERIES_COUNT = 100
_TRAILING_NUMBER_RE = re.compile(r"(\d+)$")


def _copied_task_name(data, list_id: str, task_name: str) -> str:
    existing = {t["name"] for t in data["tasks"] if t["listId"] == list_id}

    base_name = f"{task_name} Copied"
    if base_name not in existing:
        return base_name

    copy_index = 2
    while f"{base_name} {copy_index}" in existing:
        copy_index += 1

    return f"{base_name} {copy_index}"


def _series_names(base_name: str, count: int) -> list[str]:
    match = _TRAILING_NUMBER_RE.search(base_name)
    if match:
        prefix = base_name[:match.start()]
        width = len(match.group(1))
        start = int(match.group(1))
        return [f"{prefix}{str(start + i).zfill(width)}" for i in range(count)]

    return [base_name] + [f"{base_name} {i}" for i in range(2, count + 1)]


def _positive_int(value, field: str) -> int:
    try:
        value = int(value)
    except (TypeError, ValueError):
        raise ServiceError(f"{field} must be a positive integer")

    if value <= 0:
        raise ServiceError(f"{field} must be a positive integer")

    return value


# ─────────────────────────── Create / Edit ───────────────────────────

@service
def add_task(
    list_name: str,
    task_name: str,
    due: str | None = None,
    recur_interval_days: int | None = None,
    email: str | None = None,
    tz_name: str = "UTC",
):
    task_name = require_name(task_name)
    recur_interval_days = (
        _positive_int(recur_interval_days, "recurIntervalDays") if recur_interval_days is not None else None
    )

    data = db.load(email)
    lst = require_list(data, list_name)

    data["tasks"].append({
        "id": db.new_id(),
        "name": task_name,
        "listId": lst["id"],
        "due": parse_date(due) if due else None,
        "doneAt": None,
        "description": "",
        "flagged": False,
        "recurIntervalDays": recur_interval_days,
    })

    db.save(data, email)


@service
def add_task_series(
    list_name: str,
    base_name: str,
    start_due: str,
    interval_days: int,
    count: int,
    email: str | None = None,
    tz_name: str = "UTC",
):
    base_name = require_name(base_name)
    start = parse_date(start_due)
    interval_days = _positive_int(interval_days, "intervalDays")
    count = _positive_int(count, "count")

    if count > MAX_SERIES_COUNT:
        raise ServiceError(f"count must be at most {MAX_SERIES_COUNT}")

    data = db.load(email)
    lst = require_list(data, list_name)

    names = _series_names(base_name, count)
    data["tasks"].extend(
        {
            "id": db.new_id(),
            "name": name,
            "listId": lst["id"],
            "due": add_days_to_date(start, i * interval_days),
            "doneAt": None,
            "description": "",
            "flagged": False,
        }
        for i, name in enumerate(names)
    )

    db.save(data, email)


@service
def edit_task(
    task_id: str,
    new_name: str,
    due: str | None = None,
    update_due: bool = False,
    recur_interval_days: int | None = None,
    update_recur: bool = False,
    email: str | None = None,
    tz_name: str = "UTC",
):
    new_name = require_name(new_name)

    data = db.load(email)
    task = require_task_by_id(data, task_id)

    task["name"] = new_name

    if update_due:
        task["due"] = parse_date(due) if due else None

    if update_recur:
        task["recurIntervalDays"] = (
            _positive_int(recur_interval_days, "recurIntervalDays") if recur_interval_days is not None else None
        )

    db.save(data, email)


# ─────────────────────────── Delete / Move ───────────────────────────

@service
def delete_task(task_id: str, email: str | None = None, tz_name: str = "UTC"):
    data = db.load(email)
    require_task_by_id(data, task_id)

    data["tasks"] = [t for t in data["tasks"] if t["id"] != task_id]

    db.save(data, email)


@service
def move_task(task_id: str, new_list_name: str, email: str | None = None, tz_name: str = "UTC"):
    data = db.load(email)

    task = require_task_by_id(data, task_id)
    new_lst = require_list(data, new_list_name)

    task["listId"] = new_lst["id"]

    db.save(data, email)


@service
def duplicate_task(task_id: str, email: str | None = None, tz_name: str = "UTC"):
    data = db.load(email)
    task = require_task_by_id(data, task_id)

    data["tasks"] = [*data["tasks"], {
        "id": db.new_id(),
        "name": _copied_task_name(data, task["listId"], task["name"]),
        "listId": task["listId"],
        "due": task.get("due"),
        "doneAt": None,
        "description": task.get("description", ""),
        "flagged": False,
        "recurIntervalDays": task.get("recurIntervalDays"),
    }]

    db.save(data, email)


# ─────────────────────────── Completion State ───────────────────────────

@service
def done_task(task_id: str, email: str | None = None, tz_name: str = "UTC"):
    data = db.load(email)
    task = require_task_by_id(data, task_id)

    if task["doneAt"]:
        raise ServiceError(f"task '{task['name']}' is already done")

    today = today_in_timezone(tz_name)
    completed_at = utc_now()

    remove_daysheet_entries(
        data,
        task["listId"],
        DaysheetEntryType.CONTINUE,
        tz_name,
        task["name"],
        today,
    )

    add_daysheet_entry(
        data,
        task["listId"],
        DaysheetEntryType.DONE,
        task["name"],
        completed_at,
    )

    recur_interval_days = task.get("recurIntervalDays")
    if recur_interval_days:
        data["tasks"] = [t for t in data["tasks"] if t["id"] != task_id]
        data["tasks"].append({
            "id": db.new_id(),
            "name": task["name"],
            "listId": task["listId"],
            "due": add_days_to_date(today, recur_interval_days),
            "doneAt": None,
            "description": task.get("description", ""),
            "flagged": False,
            "recurIntervalDays": recur_interval_days,
        })
    else:
        task["doneAt"] = completed_at
        task["flagged"] = False

    db.save(data, email)


@service
def flag_task(task_id: str, flagged: bool, email: str | None = None, tz_name: str = "UTC"):
    data = db.load(email)
    task = require_task_by_id(data, task_id)
    task["flagged"] = flagged
    db.save(data, email)


@service
def set_task_description(task_id: str, description: str, email: str | None = None, tz_name: str = "UTC"):
    data = db.load(email)
    task = require_task_by_id(data, task_id)
    task["description"] = description
    db.save(data, email)


@service
def undo_task(task_id: str, email: str | None = None, tz_name: str = "UTC"):
    data = db.load(email)
    task = require_task_by_id(data, task_id)

    if not task["doneAt"]:
        raise ServiceError(f"task '{task['name']}' is not done")

    task["doneAt"] = None

    db.save(data, email)
