import unittest
from unittest.mock import patch

from server.constants import DaysheetEntryType
from server.services.tasks import (
    add_task,
    add_task_series,
    delete_task,
    duplicate_task,
    done_task,
    edit_task,
    flag_task,
    move_task,
    set_task_description,
    skip_task,
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
TASK_DONE = task_record(id="task-2", name="Task B", list_id="list-1", done_at="2026-04-25T01:00:00Z")

TODAY = "2026-04-26"
NOW_DT = "2026-04-26T10:00:00Z"


def make_db(*tasks, lists=None, daysheet=None):
    return db_record(
        lists=lists or [LIST_1, LIST_2],
        tasks=list(tasks),
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
        self.assertIsNone(task["doneAt"])
        self.assertEqual(task["description"], "")

    def test_add_task_with_due_date(self):
        with (
            saved_db(make_db()) as saved,
            patch("server.db.new_id", return_value="new-id"),
        ):
            result = add_task("List A", "New task", "2026-05-01")

        assert_ok(result)
        self.assertEqual(saved["tasks"][0]["due"], "2026-05-01")

    def test_add_task_allows_duplicate_name_in_same_list(self):
        with (
            saved_db(make_db(TASK_1)) as saved,
            patch("server.db.new_id", return_value="task-2"),
        ):
            result = add_task("List A", "Task A")

        assert_ok(result)
        self.assertEqual([t["name"] for t in saved["tasks"]], ["Task A", "Task A"])

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

    def test_add_task_with_recur_interval(self):
        with (
            saved_db(make_db()) as saved,
            patch("server.db.new_id", return_value="new-id"),
        ):
            result = add_task("List A", "New task", None, 7)

        assert_ok(result)
        self.assertEqual(saved["tasks"][0]["recurIntervalDays"], 7)

    def test_add_task_rejects_non_positive_recur_interval(self):
        with saved_db(make_db()):
            result = add_task("List A", "New task", None, 0)

        assert_error(result, "recurIntervalDays must be a positive integer")


class TaskSeriesTest(unittest.TestCase):

    def test_add_task_series_generates_padded_sequence(self):
        with (
            saved_db(make_db()) as saved,
            patch("server.db.new_id", side_effect=[f"id-{i}" for i in range(10)]),
        ):
            result = add_task_series("List A", "LEC 01", "2026-05-04", 7, 10)

        assert_ok(result)

        names = [t["name"] for t in saved["tasks"]]
        self.assertEqual(names, [f"LEC {i:02d}" for i in range(1, 11)])

    def test_add_task_series_spaces_due_dates_by_interval(self):
        with (
            saved_db(make_db()) as saved,
            patch("server.db.new_id", side_effect=[f"id-{i}" for i in range(4)]),
        ):
            result = add_task_series("List A", "LEC 01", "2026-05-04", 7, 4)

        assert_ok(result)

        dues = [t["due"] for t in saved["tasks"]]
        self.assertEqual(dues, ["2026-05-04", "2026-05-11", "2026-05-18", "2026-05-25"])

    def test_add_task_series_falls_back_to_suffix_without_trailing_number(self):
        with (
            saved_db(make_db()) as saved,
            patch("server.db.new_id", side_effect=[f"id-{i}" for i in range(3)]),
        ):
            result = add_task_series("List A", "Reading", "2026-05-04", 7, 3)

        assert_ok(result)

        names = [t["name"] for t in saved["tasks"]]
        self.assertEqual(names, ["Reading", "Reading 2", "Reading 3"])

    def test_add_task_series_rejects_non_positive_count(self):
        with saved_db(make_db()):
            result = add_task_series("List A", "LEC 01", "2026-05-04", 7, 0)

        assert_error(result, "count must be a positive integer")

    def test_add_task_series_rejects_count_over_max(self):
        with saved_db(make_db()):
            result = add_task_series("List A", "LEC 01", "2026-05-04", 7, 101)

        assert_error(result, "count must be at most 100")

    def test_add_task_series_rejects_non_positive_interval(self):
        with saved_db(make_db()):
            result = add_task_series("List A", "LEC 01", "2026-05-04", 0, 5)

        assert_error(result, "intervalDays must be a positive integer")

    def test_add_task_series_rejects_unknown_list(self):
        with saved_db(make_db()):
            result = add_task_series("Missing List", "LEC 01", "2026-05-04", 7, 5)

        assert_error(result, "not found")

    def test_add_task_series_rejects_invalid_start_date(self):
        with saved_db(make_db()):
            result = add_task_series("List A", "LEC 01", "not-a-date", 7, 5)

        assert_error(result, "invalid date")


class TaskEditTest(unittest.TestCase):

    def test_edit_task_renames_task(self):
        with saved_db(make_db(TASK_1)) as saved:
            result = edit_task("task-1", "Renamed task")

        assert_ok(result)
        self.assertEqual(saved["tasks"][0]["name"], "Renamed task")

    def test_edit_task_changes_due_when_requested(self):
        with saved_db(make_db(TASK_1)) as saved:
            result = edit_task(
                "task-1",
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
                "task-1",
                "Task A",
                None,
                update_due=True,
            )

        assert_ok(result)
        self.assertIsNone(saved["tasks"][0]["due"])

    def test_edit_task_preserves_due_when_not_requested(self):
        task = task_record(id="task-1", name="Task A", list_id="list-1", due="2026-05-01")

        with saved_db(make_db(task)) as saved:
            result = edit_task("task-1", "Renamed task")

        assert_ok(result)
        self.assertEqual(saved["tasks"][0]["due"], "2026-05-01")

    def test_edit_task_allows_duplicate_name(self):
        task_2 = task_record(id="task-2", name="Task B", list_id="list-1")

        with saved_db(make_db(TASK_1, task_2)) as saved:
            result = edit_task("task-1", "Task B")

        assert_ok(result)
        self.assertEqual([t["name"] for t in saved["tasks"]], ["Task B", "Task B"])

    def test_edit_task_sets_recur_interval_when_requested(self):
        with saved_db(make_db(TASK_1)) as saved:
            result = edit_task(
                "task-1",
                "Task A",
                recur_interval_days=7,
                update_recur=True,
            )

        assert_ok(result)
        self.assertEqual(saved["tasks"][0]["recurIntervalDays"], 7)

    def test_edit_task_clears_recur_interval_when_requested(self):
        task = task_record(id="task-1", name="Task A", list_id="list-1", recur_interval_days=7)

        with saved_db(make_db(task)) as saved:
            result = edit_task(
                "task-1",
                "Task A",
                recur_interval_days=None,
                update_recur=True,
            )

        assert_ok(result)
        self.assertIsNone(saved["tasks"][0]["recurIntervalDays"])

    def test_edit_task_preserves_recur_interval_when_not_requested(self):
        task = task_record(id="task-1", name="Task A", list_id="list-1", recur_interval_days=7)

        with saved_db(make_db(task)) as saved:
            result = edit_task("task-1", "Renamed task")

        assert_ok(result)
        self.assertEqual(saved["tasks"][0]["recurIntervalDays"], 7)

    def test_edit_task_rejects_unknown_task(self):
        with saved_db(make_db()):
            result = edit_task("ghost-id", "New name")

        assert_error(result, "not found")

    def test_edit_task_rejects_empty_new_name(self):
        with saved_db(make_db(TASK_1)):
            result = edit_task("task-1", "")

        assert_error(result, "name is required")


class TaskMoveDeleteTest(unittest.TestCase):

    def test_move_task_changes_list(self):
        with saved_db(make_db(TASK_1)) as saved:
            result = move_task("task-1", "List B")

        assert_ok(result)
        self.assertEqual(saved["tasks"][0]["listId"], "list-2")

    def test_move_task_allows_duplicate_in_destination(self):
        task_2 = task_record(id="task-2", name="Task A", list_id="list-2")

        with saved_db(make_db(TASK_1, task_2)) as saved:
            result = move_task("task-1", "List B")

        assert_ok(result)
        self.assertEqual(saved["tasks"][0]["listId"], "list-2")

    def test_move_task_rejects_unknown_task(self):
        with saved_db(make_db()):
            result = move_task("ghost-id", "List B")

        assert_error(result, "not found")

    def test_move_task_rejects_unknown_destination_list(self):
        with saved_db(make_db(TASK_1)):
            result = move_task("task-1", "Missing List")

        assert_error(result, "not found")

    def test_delete_task_removes_task(self):
        with saved_db(make_db(TASK_1)) as saved:
            result = delete_task("task-1")

        assert_ok(result)
        self.assertEqual(saved["tasks"], [])

    def test_delete_task_rejects_unknown_task(self):
        with saved_db(make_db()):
            result = delete_task("ghost-id")

        assert_error(result, "not found")

    def test_duplicate_task_copies_task_in_same_list(self):
        task = task_record(
            id="task-1",
            name="Task A",
            list_id="list-1",
            due="2026-05-01",
            description="Existing notes",
        )

        with (
            saved_db(make_db(task)) as saved,
            patch("server.db.new_id", return_value="task-2"),
        ):
            result = duplicate_task("task-1")

        assert_ok(result)

        duplicated = saved["tasks"][1]
        self.assertEqual(duplicated["id"], "task-2")
        self.assertEqual(duplicated["name"], "Task A Copied")
        self.assertEqual(duplicated["listId"], "list-1")
        self.assertEqual(duplicated["due"], "2026-05-01")
        self.assertIsNone(duplicated["doneAt"])
        self.assertEqual(duplicated["description"], "Existing notes")

    def test_duplicate_task_uses_incrementing_copy_name(self):
        copy = task_record(id="task-2", name="Task A Copied", list_id="list-1")

        with (
            saved_db(make_db(TASK_1, copy)) as saved,
            patch("server.db.new_id", return_value="task-3"),
        ):
            result = duplicate_task("task-1")

        assert_ok(result)
        self.assertEqual(saved["tasks"][2]["name"], "Task A Copied 2")

    def test_duplicate_task_rejects_unknown_task(self):
        with saved_db(make_db()):
            result = duplicate_task("ghost-id")

        assert_error(result, "not found")

    def test_duplicate_task_copies_recur_interval(self):
        task = task_record(id="task-1", name="Task A", list_id="list-1", recur_interval_days=7)

        with (
            saved_db(make_db(task)) as saved,
            patch("server.db.new_id", return_value="task-2"),
        ):
            result = duplicate_task("task-1")

        assert_ok(result)
        self.assertEqual(saved["tasks"][1]["recurIntervalDays"], 7)


class TaskCompletionTest(unittest.TestCase):

    def test_done_task_stamps_today(self):
        with (
            saved_db(make_db(TASK_1)) as saved,
            patch("server.services.tasks.today_in_timezone", return_value=TODAY),
            patch("server.services.tasks.utc_now", return_value=NOW_DT),
            patch("server.db.new_id", return_value="entry-1"),
        ):
            result = done_task("task-1")

        assert_ok(result)
        self.assertEqual(saved["tasks"][0]["doneAt"], NOW_DT)

    def test_done_task_adds_daysheet_entry(self):
        with (
            saved_db(make_db(TASK_1)) as saved,
            patch("server.services.tasks.today_in_timezone", return_value=TODAY),
            patch("server.services.tasks.utc_now", return_value=NOW_DT),
            patch("server.db.new_id", return_value="entry-1"),
        ):
            result = done_task("task-1")

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
            patch("server.services.tasks.today_in_timezone", return_value=TODAY),
            patch("server.services.tasks.utc_now", return_value=NOW_DT),
            patch("server.db.new_id", return_value="entry-2"),
        ):
            result = done_task("task-1")

        assert_ok(result)

        types = [entry["type"] for entry in saved["daysheet"]]
        self.assertNotIn(DaysheetEntryType.CONTINUE, types)
        self.assertIn(DaysheetEntryType.DONE, types)

    def test_done_task_rejects_already_done_task(self):
        with saved_db(make_db(TASK_DONE)):
            result = done_task("task-2")

        assert_error(result, "already done")

    def test_undo_task_clears_done(self):
        with saved_db(make_db(TASK_DONE)) as saved:
            result = undo_task("task-2")

        assert_ok(result)
        self.assertIsNone(saved["tasks"][0]["doneAt"])

    def test_undo_task_rejects_pending_task(self):
        with saved_db(make_db(TASK_1)):
            result = undo_task("task-1")

        assert_error(result, "not done")

    def test_done_task_replaces_recurring_task_with_next_occurrence(self):
        task = task_record(id="task-1", name="Task A", list_id="list-1", due="2026-04-20", recur_interval_days=7)

        with (
            saved_db(make_db(task)) as saved,
            patch("server.services.tasks.today_in_timezone", return_value=TODAY),
            patch("server.services.tasks.utc_now", return_value=NOW_DT),
            patch("server.db.new_id", side_effect=["entry-1", "task-2"]),
        ):
            result = done_task("task-1")

        assert_ok(result)

        self.assertEqual(len(saved["tasks"]), 1)
        spawned = saved["tasks"][0]
        self.assertEqual(spawned["id"], "task-2")
        self.assertEqual(spawned["name"], "Task A")
        self.assertEqual(spawned["listId"], "list-1")
        self.assertEqual(spawned["due"], "2026-04-27")
        self.assertIsNone(spawned["doneAt"])
        self.assertEqual(spawned["recurIntervalDays"], 7)

    def test_done_task_bases_next_due_on_prior_due_not_today(self):
        task = task_record(id="task-1", name="Task A", list_id="list-1", due="2026-04-27", recur_interval_days=1)

        with (
            saved_db(make_db(task)) as saved,
            patch("server.services.tasks.today_in_timezone", return_value=TODAY),
            patch("server.services.tasks.utc_now", return_value=NOW_DT),
            patch("server.db.new_id", side_effect=["entry-1", "task-2"]),
        ):
            result = done_task("task-1")

        assert_ok(result)
        self.assertEqual(saved["tasks"][0]["due"], "2026-04-28")

    def test_done_task_falls_back_to_today_when_recurring_task_has_no_due(self):
        task = task_record(id="task-1", name="Task A", list_id="list-1", due=None, recur_interval_days=7)

        with (
            saved_db(make_db(task)) as saved,
            patch("server.services.tasks.today_in_timezone", return_value=TODAY),
            patch("server.services.tasks.utc_now", return_value=NOW_DT),
            patch("server.db.new_id", side_effect=["entry-1", "task-2"]),
        ):
            result = done_task("task-1")

        assert_ok(result)
        self.assertEqual(saved["tasks"][0]["due"], "2026-05-03")

    def test_done_task_does_not_spawn_next_occurrence_for_plain_task(self):
        with (
            saved_db(make_db(TASK_1)) as saved,
            patch("server.services.tasks.today_in_timezone", return_value=TODAY),
            patch("server.services.tasks.utc_now", return_value=NOW_DT),
            patch("server.db.new_id", return_value="entry-1"),
        ):
            result = done_task("task-1")

        assert_ok(result)
        self.assertEqual(len(saved["tasks"]), 1)

    def test_done_task_logs_daysheet_entry_for_recurring_task(self):
        task = task_record(id="task-1", name="Task A", list_id="list-1", recur_interval_days=7)

        with (
            saved_db(make_db(task)) as saved,
            patch("server.services.tasks.today_in_timezone", return_value=TODAY),
            patch("server.services.tasks.utc_now", return_value=NOW_DT),
            patch("server.db.new_id", return_value="entry-1"),
        ):
            result = done_task("task-1")

        assert_ok(result)

        entry = saved["daysheet"][0]
        self.assertEqual(entry["type"], DaysheetEntryType.DONE)
        self.assertEqual(entry["text"], "Task A")

    def test_done_task_allows_completing_two_same_named_tasks_same_day(self):
        task_a = task_record(id="task-1", name="Task A", list_id="list-1")
        task_b = task_record(id="task-2", name="Task A", list_id="list-1")

        with (
            saved_db(make_db(task_a, task_b)) as saved,
            patch("server.services.tasks.today_in_timezone", return_value=TODAY),
            patch("server.services.tasks.utc_now", return_value=NOW_DT),
            patch("server.db.new_id", side_effect=["entry-1", "entry-2"]),
        ):
            first = done_task("task-1")
            second = done_task("task-2")

        assert_ok(first)
        assert_ok(second)
        self.assertIsNotNone(saved["tasks"][0]["doneAt"])
        self.assertIsNotNone(saved["tasks"][1]["doneAt"])

    def test_done_task_rejects_recompleting_the_same_recurring_occurrence(self):
        task = task_record(id="task-1", name="Task A", list_id="list-1", recur_interval_days=7)

        with (
            saved_db(make_db(task)) as saved,
            patch("server.services.tasks.today_in_timezone", return_value=TODAY),
            patch("server.services.tasks.utc_now", return_value=NOW_DT),
            patch("server.db.new_id", side_effect=["entry-1", "task-2"]),
        ):
            first = done_task("task-1")
            second = done_task("task-1")

        assert_ok(first)
        assert_error(second, "not found")
        self.assertEqual(len(saved["tasks"]), 1)

    def test_done_task_clears_flag(self):
        task = task_record(id="task-1", name="Task A", list_id="list-1", flagged=True)

        with (
            saved_db(make_db(task)) as saved,
            patch("server.services.tasks.today_in_timezone", return_value=TODAY),
            patch("server.services.tasks.utc_now", return_value=NOW_DT),
            patch("server.db.new_id", return_value="entry-1"),
        ):
            result = done_task("task-1")

        assert_ok(result)
        self.assertFalse(saved["tasks"][0]["flagged"])


class TaskSkipTest(unittest.TestCase):

    def test_skip_task_replaces_recurring_task_with_next_occurrence(self):
        task = task_record(id="task-1", name="Task A", list_id="list-1", due="2026-04-20", recur_interval_days=7)

        with (
            saved_db(make_db(task)) as saved,
            patch("server.services.tasks.today_in_timezone", return_value=TODAY),
            patch("server.db.new_id", return_value="task-2"),
        ):
            result = skip_task("task-1")

        assert_ok(result)
        self.assertEqual(len(saved["tasks"]), 1)

        spawned = saved["tasks"][0]
        self.assertEqual(spawned["id"], "task-2")
        self.assertEqual(spawned["name"], "Task A")
        self.assertEqual(spawned["due"], "2026-04-27")
        self.assertIsNone(spawned["doneAt"])
        self.assertEqual(spawned["recurIntervalDays"], 7)

    def test_skip_task_does_not_log_daysheet_entry(self):
        task = task_record(id="task-1", name="Task A", list_id="list-1", recur_interval_days=7)

        with (
            saved_db(make_db(task)) as saved,
            patch("server.services.tasks.today_in_timezone", return_value=TODAY),
            patch("server.db.new_id", return_value="task-2"),
        ):
            result = skip_task("task-1")

        assert_ok(result)
        self.assertEqual(saved["daysheet"], [])

    def test_skip_task_rejects_non_recurring_task(self):
        with saved_db(make_db(TASK_1)):
            result = skip_task("task-1")

        assert_error(result, "not recurring")

    def test_skip_task_rejects_unknown_task(self):
        with saved_db(make_db()):
            result = skip_task("ghost-id")

        assert_error(result, "not found")


class TaskFlagTest(unittest.TestCase):

    def test_flag_task_sets_flag(self):
        with saved_db(make_db(TASK_1)) as saved:
            result = flag_task("task-1", True)

        assert_ok(result)
        self.assertTrue(saved["tasks"][0]["flagged"])

    def test_flag_task_unsets_flag(self):
        task = task_record(id="task-1", name="Task A", list_id="list-1", flagged=True)

        with saved_db(make_db(task)) as saved:
            result = flag_task("task-1", False)

        assert_ok(result)
        self.assertFalse(saved["tasks"][0]["flagged"])

    def test_flag_task_rejects_unknown_task(self):
        with saved_db(make_db()):
            result = flag_task("ghost-id", True)

        assert_error(result, "not found")


class TaskDescriptionTest(unittest.TestCase):

    def test_set_description_updates_task(self):
        with saved_db(make_db(TASK_1)) as saved:
            result = set_task_description("task-1", "Some notes here")

        assert_ok(result)
        self.assertEqual(saved["tasks"][0]["description"], "Some notes here")

    def test_set_description_allows_empty_string(self):
        task = task_record(id="task-1", name="Task A", list_id="list-1", description="Existing notes")

        with saved_db(make_db(task)) as saved:
            result = set_task_description("task-1", "")

        assert_ok(result)
        self.assertEqual(saved["tasks"][0]["description"], "")

    def test_set_description_rejects_unknown_task(self):
        with saved_db(make_db()):
            result = set_task_description("ghost-id", "Notes")

        assert_error(result, "not found")


if __name__ == "__main__":
    unittest.main()
