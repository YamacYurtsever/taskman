from server import db
from server.constants import DaysheetEntryType
from server.services.utils import (
    ServiceError,
    add_daysheet_entry,
    find_task,
    now,
    parse_date,
    remove_daysheet_entries,
    require_list,
    require_name,
    require_task,
    service,
    today,
)


# ─────────────────────────── Create / Edit ───────────────────────────

@service
def add_task(list_name: str, task_name: str, due: str | None = None):
    task_name = require_name(task_name)

    data = db.load()
    lst = require_list(data, list_name)

    if find_task(data, lst["id"], task_name):
        raise ServiceError(f"task '{task_name}' already exists in '{list_name}'")

    data["tasks"].append({
        "id": db.new_id(),
        "name": task_name,
        "listId": lst["id"],
        "due": parse_date(due) if due else None,
        "done": None,
        "description": "",
    })

    db.save(data)


@service
def edit_task(
    list_name: str,
    task_name: str,
    new_name: str | None = None,
    due: str | None = None,
    update_due: bool = False,
):
    if new_name is None:
        new_name = task_name
    new_name = require_name(new_name)

    data = db.load()
    lst = require_list(data, list_name)
    task = require_task(data, lst, task_name)

    if new_name != task_name and find_task(data, lst["id"], new_name):
        raise ServiceError(f"task '{new_name}' already exists in '{list_name}'")

    task["name"] = new_name

    if update_due:
        task["due"] = parse_date(due) if due else None

    db.save(data)


# ─────────────────────────── Delete / Move ───────────────────────────

@service
def delete_task(list_name: str, task_name: str):
    data = db.load()
    lst = require_list(data, list_name)
    task = require_task(data, lst, task_name)

    data["tasks"] = [t for t in data["tasks"] if t["id"] != task["id"]]

    db.save(data)


@service
def move_task(list_name: str, task_name: str, new_list_name: str):
    data = db.load()

    lst = require_list(data, list_name)
    task = require_task(data, lst, task_name)
    new_lst = require_list(data, new_list_name)

    if find_task(data, new_lst["id"], task_name):
        raise ServiceError(f"task '{task_name}' already exists in '{new_list_name}'")

    task["listId"] = new_lst["id"]

    db.save(data)


# ─────────────────────────── Completion State ───────────────────────────

@service
def done_task(list_name: str, task_name: str):
    data = db.load()

    lst = require_list(data, list_name)
    task = require_task(data, lst, task_name)

    if task["done"]:
        raise ServiceError(f"task '{task_name}' is already done")

    remove_daysheet_entries(
        data,
        lst["id"],
        DaysheetEntryType.CONTINUE,
        task_name,
        today(),
    )

    add_daysheet_entry(
        data,
        lst["id"],
        DaysheetEntryType.DONE,
        task_name,
        now(),
    )

    task["done"] = today()

    db.save(data)


@service
def set_task_description(list_name: str, task_name: str, description: str):
    data = db.load()
    lst = require_list(data, list_name)
    task = require_task(data, lst, task_name)
    task["description"] = description
    db.save(data)


@service
def undo_task(list_name: str, task_name: str):
    data = db.load()

    lst = require_list(data, list_name)
    task = require_task(data, lst, task_name)

    if not task["done"]:
        raise ServiceError(f"task '{task_name}' is not done")

    task["done"] = None

    db.save(data)
