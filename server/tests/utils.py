import copy
from contextlib import contextmanager
from unittest.mock import patch

from server.constants import DaysheetEntryType


# ─────────────────────────── Records ───────────────────────────

def group_record(id="group-1", name="Group"):
    return {
        "id": id,
        "name": name,
    }


def list_record(id="list-1", name="List A", group_id=None):
    return {
        "id": id,
        "name": name,
        "groupId": group_id,
    }


def task_record(id="task-1", name="Task A", list_id="list-1", due=None, done=None, description=""):
    return {
        "id": id,
        "name": name,
        "listId": list_id,
        "due": due,
        "done": done,
        "description": description,
    }


def daysheet_entry(
    id="entry-1",
    datetime="2026-04-26T10:00:00",
    list_id="list-1",
    type=DaysheetEntryType.LOG,
    text="Entry",
):
    return {
        "id": id,
        "datetime": datetime,
        "listId": list_id,
        "type": type,
        "text": text,
    }


# ─────────────────────────── Shared Fixtures ───────────────────────────

GROUP_1 = group_record(id="group-1", name="Group")
LIST_1 = list_record(id="list-1", name="List A")
LIST_2 = list_record(id="list-2", name="List B")
TASK_1 = task_record(id="task-1", name="Task A", list_id="list-1")
TASK_DONE = task_record(id="task-2", name="Task B", list_id="list-1", done="2026-04-25")

TODAY = "2026-04-26"
NOW_DT = "2026-04-26T10:00:00"


# ─────────────────────────── DB Fixtures ───────────────────────────

def db_record(groups=None, lists=None, tasks=None, daysheet=None):
    return {
        "groups": copy.deepcopy(groups or []),
        "lists": copy.deepcopy(lists or []),
        "tasks": copy.deepcopy(tasks or []),
        "daysheet": copy.deepcopy(daysheet or []),
    }


def make_db(*tasks, groups=None, lists=None, daysheet=None):
    return db_record(
        groups=groups or [],
        lists=lists or [LIST_1, LIST_2],
        tasks=tasks,
        daysheet=daysheet or [],
    )


def basic_db():
    return db_record(
        groups=[GROUP_1],
        lists=[
            list_record(id="list-1", name="List A", group_id="group-1"),
            LIST_2,
        ],
        tasks=[TASK_1, TASK_DONE],
    )


# ─────────────────────────── Assertions ───────────────────────────

def assert_ok(result):
    ok, message = result
    assert ok, message


def assert_error(result, contains=None):
    ok, message = result
    assert not ok

    if contains is not None:
        assert contains in message


# ─────────────────────────── DB Patching ───────────────────────────

@contextmanager
def saved_db(initial_data):
    saved = {}

    def save(next_data):
        saved.clear()
        saved.update(copy.deepcopy(next_data))

    with (
        patch("server.db.load", return_value=copy.deepcopy(initial_data)),
        patch("server.db.save", side_effect=save),
    ):
        yield saved
