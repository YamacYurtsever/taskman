import unittest
from unittest.mock import patch

from server.constants import DaysheetEntryType
from server.services.daysheet import add_log, continue_task
from server.tests.utils import (
    NOW_DT,
    TASK_1,
    TODAY,
    assert_error,
    assert_ok,
    daysheet_entry,
    make_db,
    saved_db,
)


class DaysheetLogTest(unittest.TestCase):

    def test_add_log_uses_current_time_for_today(self):
        with (
            saved_db(make_db(TASK_1)) as saved,
            patch("server.services.daysheet.today_in_timezone", return_value=TODAY),
            patch("server.services.daysheet.utc_now", return_value=NOW_DT),
            patch("server.db.new_id", return_value="entry-1"),
        ):
            result = add_log("List A", "Talked with team", TODAY)

        assert_ok(result)
        self.assertEqual(saved["daysheet"][0]["datetime"], NOW_DT)

    def test_add_log_uses_end_of_selected_day_for_past_days(self):
        with (
            saved_db(make_db(TASK_1)) as saved,
            patch("server.services.daysheet.today_in_timezone", return_value=TODAY),
            patch("server.db.new_id", return_value="entry-1"),
        ):
            result = add_log("List A", "Wrapped up", "2026-04-25")

        assert_ok(result)
        self.assertEqual(saved["daysheet"][0]["datetime"], "2026-04-25T23:59:00Z")

    def test_add_log_uses_start_of_selected_day_for_future_days(self):
        with (
            saved_db(make_db(TASK_1)) as saved,
            patch("server.services.daysheet.today_in_timezone", return_value=TODAY),
            patch("server.db.new_id", return_value="entry-1"),
        ):
            result = add_log("List A", "Planned ahead", "2026-04-30")

        assert_ok(result)
        self.assertEqual(saved["daysheet"][0]["datetime"], "2026-04-30T00:00:00Z")


class ContinueTaskTest(unittest.TestCase):

    def test_continue_task_adds_daysheet_entry(self):
        with (
            saved_db(make_db(TASK_1)) as saved,
            patch("server.services.daysheet.today_in_timezone", return_value=TODAY),
            patch("server.services.daysheet.utc_now", return_value=NOW_DT),
            patch("server.db.new_id", return_value="entry-1"),
        ):
            result = continue_task("task-1")

        assert_ok(result)

        entry = saved["daysheet"][0]
        self.assertEqual(entry["type"], DaysheetEntryType.CONTINUE)
        self.assertEqual(entry["text"], "Task A")
        self.assertEqual(entry["listId"], "list-1")

    def test_continue_task_rejects_unknown_task(self):
        with saved_db(make_db()):
            result = continue_task("ghost-id")

        assert_error(result, "not found")

    def test_continue_task_rejects_already_finished_today(self):
        entry = daysheet_entry(
            id="entry-1",
            datetime=NOW_DT,
            list_id="list-1",
            type=DaysheetEntryType.DONE,
            text="Task A",
        )

        with (
            saved_db(make_db(TASK_1, daysheet=[entry])),
            patch("server.services.daysheet.today_in_timezone", return_value=TODAY),
        ):
            result = continue_task("task-1")

        assert_error(result, "already finished today")

    def test_continue_task_rejects_already_continued_today(self):
        entry = daysheet_entry(
            id="entry-1",
            datetime=NOW_DT,
            list_id="list-1",
            type=DaysheetEntryType.CONTINUE,
            text="Task A",
        )

        with (
            saved_db(make_db(TASK_1, daysheet=[entry])),
            patch("server.services.daysheet.today_in_timezone", return_value=TODAY),
        ):
            result = continue_task("task-1")

        assert_error(result, "already continued today")


if __name__ == "__main__":
    unittest.main()
