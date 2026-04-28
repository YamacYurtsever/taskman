from server import db
from server.constants import DaysheetEntryType
from server.services.utils import (
    ServiceError,
    add_daysheet_entry,
    find_task,
    parse_date,
    remove_daysheet_entries,
    require_list,
    require_name,
    require_task,
    service,
    today_in_timezone,
    utc_now,
)


def _copied_task_name(data, list_id: str, task_name: str) -> str:
    base_name = f"{task_name} Copied"
    candidate = base_name
    copy_index = 2

    while find_task(data, list_id, candidate):
        candidate = f"{base_name} {copy_index}"
        copy_index += 1

    return candidate


# ─────────────────────────── Create / Edit ───────────────────────────

@service
def add_task(list_name: str, task_name: str, due: str | None = None, email: str | None = None, tz_name: str = "UTC"):
    task_name = require_name(task_name)

    data = db.load(email)
    lst = require_list(data, list_name)

    if find_task(data, lst["id"], task_name):
        raise ServiceError(f"task '{task_name}' already exists in '{list_name}'")

    data["tasks"].append({
        "id": db.new_id(),
        "name": task_name,
        "listId": lst["id"],
        "due": parse_date(due) if due else None,
        "doneAt": None,
        "description": "",
    })

    db.save(data, email)


@service
def edit_task(
    list_name: str,
    task_name: str,
    new_name: str | None = None,
    due: str | None = None,
    update_due: bool = False,
    email: str | None = None,
    tz_name: str = "UTC",
):
    if new_name is None:
        new_name = task_name
    new_name = require_name(new_name)

    data = db.load(email)
    lst = require_list(data, list_name)
    task = require_task(data, lst, task_name)

    if new_name != task_name and find_task(data, lst["id"], new_name):
        raise ServiceError(f"task '{new_name}' already exists in '{list_name}'")

    task["name"] = new_name

    if update_due:
        task["due"] = parse_date(due) if due else None

    db.save(data, email)


# ─────────────────────────── Delete / Move ───────────────────────────

@service
def delete_task(list_name: str, task_name: str, email: str | None = None, tz_name: str = "UTC"):
    data = db.load(email)
    lst = require_list(data, list_name)
    task = require_task(data, lst, task_name)

    data["tasks"] = [t for t in data["tasks"] if t["id"] != task["id"]]

    db.save(data, email)


@service
def move_task(list_name: str, task_name: str, new_list_name: str, email: str | None = None, tz_name: str = "UTC"):
    data = db.load(email)

    lst = require_list(data, list_name)
    task = require_task(data, lst, task_name)
    new_lst = require_list(data, new_list_name)

    if find_task(data, new_lst["id"], task_name):
        raise ServiceError(f"task '{task_name}' already exists in '{new_list_name}'")

    task["listId"] = new_lst["id"]

    db.save(data, email)


@service
def duplicate_task(list_name: str, task_name: str, email: str | None = None, tz_name: str = "UTC"):
    data = db.load(email)
    lst = require_list(data, list_name)
    task = require_task(data, lst, task_name)

    data["tasks"] = [*data["tasks"], {
        "id": db.new_id(),
        "name": _copied_task_name(data, lst["id"], task_name),
        "listId": lst["id"],
        "due": task.get("due"),
        "doneAt": None,
        "description": task.get("description", ""),
    }]

    db.save(data, email)


# ─────────────────────────── Completion State ───────────────────────────

@service
def done_task(list_name: str, task_name: str, email: str | None = None, tz_name: str = "UTC"):
    data = db.load(email)

    lst = require_list(data, list_name)
    task = require_task(data, lst, task_name)

    if task["doneAt"]:
        raise ServiceError(f"task '{task_name}' is already done")

    today = today_in_timezone(tz_name)
    completed_at = utc_now()

    remove_daysheet_entries(
        data,
        lst["id"],
        DaysheetEntryType.CONTINUE,
        tz_name,
        task_name,
        today,
    )

    add_daysheet_entry(
        data,
        lst["id"],
        DaysheetEntryType.DONE,
        task_name,
        completed_at,
    )

    task["doneAt"] = completed_at

    db.save(data, email)


@service
def set_task_description(list_name: str, task_name: str, description: str, email: str | None = None, tz_name: str = "UTC"):
    data = db.load(email)
    lst = require_list(data, list_name)
    task = require_task(data, lst, task_name)
    task["description"] = description
    db.save(data, email)


@service
def undo_task(list_name: str, task_name: str, email: str | None = None, tz_name: str = "UTC"):
    data = db.load(email)

    lst = require_list(data, list_name)
    task = require_task(data, lst, task_name)

    if not task["doneAt"]:
        raise ServiceError(f"task '{task_name}' is not done")

    task["doneAt"] = None

    db.save(data, email)
