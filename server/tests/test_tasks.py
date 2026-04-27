import unittest
from unittest.mock import patch

from server.constants import DaysheetEntryType
from server.services.tasks import (
    add_task,
    delete_task,
    done_task,
    edit_task,
    move_task,
    set_task_description,
    undo_task,
)
from server.tests.utils import (
    assert_error,
    assert_ok,
    db_record,
    daysheet_entry,
    list_record,
    saved_db,
    task_record,
)


LIST_1 = list_record(id="list-1", name="List A")
LIST_2 = list_record(id="list-2", name="List B")
TASK_1 = task_record(id="task-1", name="Task A", list_id="list-1")
TASK_DONE = task_record(id="task-2", name="Task B", list_id="list-1", done="2026-04-25")

TODAY = "2026-04-26"
NOW_DT = "2026-04-26T10:00:00"


def make_db(*tasks, lists=None, daysheet=None):
    return db_record(
        lists=lists or [LIST_1, LIST_2],
        tasks=tasks,
        daysheet=daysheet or [],
    )


class TaskCreateTest(unittest.TestCase):

    def test_add_task_creates_task(self):
        with (
            saved_db(make_db()) as saved,
            patch("server.db.new_id", return_value="new-id"),
        ):
            result = add_task("List A", "New task")

        assert_ok(result)

        task = saved["tasks"][0]
        self.assertEqual(task["id"], "new-id")
        self.assertEqual(task["name"], "New task")
        self.assertEqual(task["listId"], "list-1")
        self.assertIsNone(task["due"])
        self.assertIsNone(task["done"])
        self.assertEqual(task["description"], "")

    def test_add_task_with_due_date(self):
        with (
            saved_db(make_db()) as saved,
            patch("server.db.new_id", return_value="new-id"),
        ):
            result = add_task("List A", "New task", "2026-05-01")

        assert_ok(result)
        self.assertEqual(saved["tasks"][0]["due"], "2026-05-01")

    def test_add_task_rejects_duplicate_name_in_same_list(self):
        with saved_db(make_db(TASK_1)):
            result = add_task("List A", "Task A")

        assert_error(result, "already exists")

    def test_add_task_rejects_unknown_list(self):
        with saved_db(make_db()):
            result = add_task("Missing List", "New task")

        assert_error(result, "not found")

    def test_add_task_rejects_empty_name(self):
        with saved_db(make_db()):
            result = add_task("List A", "")

        assert_error(result, "name is required")

    def test_add_task_rejects_invalid_due_date(self):
        with saved_db(make_db()):
            result = add_task("List A", "New task", "not-a-date")

        assert_error(result, "invalid date")


class TaskEditTest(unittest.TestCase):

    def test_edit_task_renames_task(self):
        with saved_db(make_db(TASK_1)) as saved:
            result = edit_task("List A", "Task A", "Renamed task")

        assert_ok(result)
        self.assertEqual(saved["tasks"][0]["name"], "Renamed task")

    def test_edit_task_changes_due_when_requested(self):
        with saved_db(make_db(TASK_1)) as saved:
            result = edit_task(
                "List A",
                "Task A",
                "Task A",
                "2026-06-01",
                update_due=True,
            )

        assert_ok(result)
        self.assertEqual(saved["tasks"][0]["due"], "2026-06-01")

    def test_edit_task_clears_due_when_requested(self):
        task = task_record(id="task-1", name="Task A", list_id="list-1", due="2026-05-01")

        with saved_db(make_db(task)) as saved:
            result = edit_task(
                "List A",
                "Task A",
                "Task A",
                None,
                update_due=True,
            )

        assert_ok(result)
        self.assertIsNone(saved["tasks"][0]["due"])

    def test_edit_task_preserves_due_when_not_requested(self):
        task = task_record(id="task-1", name="Task A", list_id="list-1", due="2026-05-01")

        with saved_db(make_db(task)) as saved:
            result = edit_task("List A", "Task A", "Renamed task")

        assert_ok(result)
        self.assertEqual(saved["tasks"][0]["due"], "2026-05-01")

    def test_edit_task_rejects_duplicate_name(self):
        task_2 = task_record(id="task-2", name="Task B", list_id="list-1")

        with saved_db(make_db(TASK_1, task_2)):
            result = edit_task("List A", "Task A", "Task B")

        assert_error(result, "already exists")

    def test_edit_task_rejects_unknown_task(self):
        with saved_db(make_db()):
            result = edit_task("List A", "Ghost task", "New name")

        assert_error(result, "not found")

    def test_edit_task_rejects_empty_new_name(self):
        with saved_db(make_db(TASK_1)):
            result = edit_task("List A", "Task A", "")

        assert_error(result, "name is required")


class TaskMoveDeleteTest(unittest.TestCase):

    def test_move_task_changes_list(self):
        with saved_db(make_db(TASK_1)) as saved:
            result = move_task("List A", "Task A", "List B")

        assert_ok(result)
        self.assertEqual(saved["tasks"][0]["listId"], "list-2")

    def test_move_task_rejects_duplicate_in_destination(self):
        task_2 = task_record(id="task-2", name="Task A", list_id="list-2")

        with saved_db(make_db(TASK_1, task_2)):
            result = move_task("List A", "Task A", "List B")

        assert_error(result, "already exists")

    def test_move_task_rejects_unknown_task(self):
        with saved_db(make_db()):
            result = move_task("List A", "Ghost task", "List B")

        assert_error(result, "not found")

    def test_move_task_rejects_unknown_destination_list(self):
        with saved_db(make_db(TASK_1)):
            result = move_task("List A", "Task A", "Missing List")

        assert_error(result, "not found")

    def test_delete_task_removes_task(self):
        with saved_db(make_db(TASK_1)) as saved:
            result = delete_task("List A", "Task A")

        assert_ok(result)
        self.assertEqual(saved["tasks"], [])

    def test_delete_task_rejects_unknown_task(self):
        with saved_db(make_db()):
            result = delete_task("List A", "Ghost task")

        assert_error(result, "not found")


class TaskCompletionTest(unittest.TestCase):

    def test_done_task_stamps_today(self):
        with (
            saved_db(make_db(TASK_1)) as saved,
            patch("server.services.utils.date") as mock_date,
            patch("server.services.tasks.now", return_value=NOW_DT),
            patch("server.db.new_id", return_value="entry-1"),
        ):
            mock_date.today.return_value.isoformat.return_value = TODAY
            result = done_task("List A", "Task A")

        assert_ok(result)
        self.assertEqual(saved["tasks"][0]["done"], TODAY)

    def test_done_task_adds_daysheet_entry(self):
        with (
            saved_db(make_db(TASK_1)) as saved,
            patch("server.services.utils.date") as mock_date,
            patch("server.services.tasks.now", return_value=NOW_DT),
            patch("server.db.new_id", return_value="entry-1"),
        ):
            mock_date.today.return_value.isoformat.return_value = TODAY
            result = done_task("List A", "Task A")

        assert_ok(result)

        entry = saved["daysheet"][0]
        self.assertEqual(entry["id"], "entry-1")
        self.assertEqual(entry["type"], DaysheetEntryType.DONE)
        self.assertEqual(entry["text"], "Task A")
        self.assertEqual(entry["datetime"], NOW_DT)

    def test_done_task_removes_continue_entry_for_today(self):
        entry = daysheet_entry(
            id="entry-1",
            datetime=NOW_DT,
            type=DaysheetEntryType.CONTINUE,
            text="Task A",
        )

        with (
            saved_db(make_db(TASK_1, daysheet=[entry])) as saved,
            patch("server.services.utils.date") as mock_date,
            patch("server.services.tasks.now", return_value=NOW_DT),
            patch("server.db.new_id", return_value="entry-2"),
        ):
            mock_date.today.return_value.isoformat.return_value = TODAY
            result = done_task("List A", "Task A")

        assert_ok(result)

        types = [entry["type"] for entry in saved["daysheet"]]
        self.assertNotIn(DaysheetEntryType.CONTINUE, types)
        self.assertIn(DaysheetEntryType.DONE, types)

    def test_done_task_rejects_already_done_task(self):
        with saved_db(make_db(TASK_DONE)):
            result = done_task("List A", "Task B")

        assert_error(result, "already done")

    def test_undo_task_clears_done(self):
        with saved_db(make_db(TASK_DONE)) as saved:
            result = undo_task("List A", "Task B")

        assert_ok(result)
        self.assertIsNone(saved["tasks"][0]["done"])

    def test_undo_task_rejects_pending_task(self):
        with saved_db(make_db(TASK_1)):
            result = undo_task("List A", "Task A")

        assert_error(result, "not done")


class TaskDescriptionTest(unittest.TestCase):

    def test_set_description_updates_task(self):
        with saved_db(make_db(TASK_1)) as saved:
            result = set_task_description("List A", "Task A", "Some notes here")

        assert_ok(result)
        self.assertEqual(saved["tasks"][0]["description"], "Some notes here")

    def test_set_description_allows_empty_string(self):
        task = task_record(id="task-1", name="Task A", list_id="list-1", description="Existing notes")

        with saved_db(make_db(task)) as saved:
            result = set_task_description("List A", "Task A", "")

        assert_ok(result)
        self.assertEqual(saved["tasks"][0]["description"], "")

    def test_set_description_rejects_unknown_task(self):
        with saved_db(make_db()):
            result = set_task_description("List A", "Ghost task", "Notes")

        assert_error(result, "not found")

    def test_set_description_rejects_unknown_list(self):
        with saved_db(make_db(TASK_1)):
            result = set_task_description("Missing List", "Task A", "Notes")

        assert_error(result, "not found")


if __name__ == "__main__":
    unittest.main()
