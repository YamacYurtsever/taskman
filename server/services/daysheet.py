from server import db
from server.constants import DaysheetEntryType
from server.services.utils import (
    ServiceError,
    add_daysheet_entry,
    find_daysheet_entry,
    has_daysheet_entry,
    remove_daysheet_entries,
    require_list,
    require_name,
    require_task,
    service,
    storage_datetime_for_local_date,
    today_in_timezone,
    utc_now,
)


# ─────────────────────────── Logs ───────────────────────────

@service
def add_log(
    list_name: str,
    text: str,
    entry_day: str | None = None,
    email: str | None = None,
    tz_name: str = "UTC",
):
    text = require_name(text, "text")

    data = db.load(email)
    lst = require_list(data, list_name)

    target_day = entry_day or today_in_timezone(tz_name)
    timestamp = storage_datetime_for_local_date(target_day, tz_name)
    add_daysheet_entry(data, lst["id"], DaysheetEntryType.LOG, text, timestamp)

    db.save(data, email)


@service
def edit_log(list_name: str, text: str, new_text: str, email: str | None = None, tz_name: str = "UTC"):
    text = require_name(text, "text")
    new_text = require_name(new_text, "new text")

    data = db.load(email)
    lst = require_list(data, list_name)

    entry = find_daysheet_entry(
        data, lst["id"], DaysheetEntryType.LOG, text, today_in_timezone(tz_name), tz_name,
    )
    if not entry:
        raise ServiceError(f"log entry '{text}' not found")

    entry["text"] = new_text
    db.save(data, email)


@service
def delete_log(list_name: str, text: str, email: str | None = None, tz_name: str = "UTC"):
    text = require_name(text, "text")

    data = db.load(email)
    lst = require_list(data, list_name)

    deleted = remove_daysheet_entries(
        data,
        lst["id"],
        DaysheetEntryType.LOG,
        tz_name,
        text,
        today_in_timezone(tz_name),
    )

    if not deleted:
        raise ServiceError(f"log entry '{text}' not found")

    db.save(data, email)


# ─────────────────────────── Continue Entries ───────────────────────────

@service
def continue_task(list_name: str, task_name: str, email: str | None = None, tz_name: str = "UTC"):
    task_name = require_name(task_name, "task")

    data = db.load(email)
    lst = require_list(data, list_name)
    require_task(data, lst, task_name)

    today = today_in_timezone(tz_name)

    if has_daysheet_entry(data, lst["id"], DaysheetEntryType.DONE, task_name, today, tz_name):
        raise ServiceError(f"'{task_name}' was already finished today")

    if has_daysheet_entry(data, lst["id"], DaysheetEntryType.CONTINUE, task_name, today, tz_name):
        raise ServiceError(f"'{task_name}' was already continued today")

    add_daysheet_entry(data, lst["id"], DaysheetEntryType.CONTINUE, task_name, utc_now())

    db.save(data, email)
