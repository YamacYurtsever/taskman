import copy
from contextlib import contextmanager
from unittest.mock import patch

from cachelib.file import FileSystemCache

from server.constants import DaysheetEntryType

TEST_CONFIG = {
    "TESTING": True,
    "SECRET_KEY": "test-secret",
    "SESSION_TYPE": "cachelib",
    "SESSION_CACHELIB": FileSystemCache("/tmp/taskman-test-sessions"),
}


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


def task_record(
    id="task-1",
    name="Task A",
    list_id="list-1",
    due=None,
    done_at=None,
    description="",
    flagged=False,
    recur_interval_days=None,
):
    return {
        "id": id,
        "name": name,
        "listId": list_id,
        "due": due,
        "doneAt": done_at,
        "description": description,
        "flagged": flagged,
        "recurIntervalDays": recur_interval_days,
    }


def daysheet_entry(
    id="entry-1",
    datetime="2026-04-26T10:00:00Z",
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
TASK_DONE = task_record(id="task-2", name="Task B", list_id="list-1", done_at="2026-04-25T01:00:00Z")

TODAY = "2026-04-26"
NOW_DT = "2026-04-26T10:00:00Z"


# ─────────────────────────── DB Fixtures ───────────────────────────

def db_record(groups=None, lists=None, tasks=None, daysheet=None):
    return {
        "groups": copy.deepcopy(list(groups or [])),
        "lists": copy.deepcopy(list(lists or [])),
        "tasks": copy.deepcopy(list(tasks or [])),
        "daysheet": copy.deepcopy(list(daysheet or [])),
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

    def save(next_data, *args, **kwargs):
        saved.clear()
        saved.update(copy.deepcopy(next_data))

    with (
        patch("server.db.load", return_value=copy.deepcopy(initial_data)),
        patch("server.db.save", side_effect=save),
    ):
        yield saved


@contextmanager
def saved_config(initial_data):
    saved = {}

    def save(next_data, *args, **kwargs):
        saved.clear()
        saved.update(copy.deepcopy(next_data))

    with (
        patch("server.config.load", return_value=copy.deepcopy(initial_data)),
        patch("server.config.save", side_effect=save),
    ):
        yield saved
