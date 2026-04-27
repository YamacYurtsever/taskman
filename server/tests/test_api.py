import unittest
from unittest.mock import patch

from server import create_app
from server.constants import DaysheetEntryType
from server.tests.utils import (
    GROUP_1,
    LIST_1,
    LIST_2,
    NOW_DT,
    TASK_1,
    TASK_DONE,
    TODAY,
    daysheet_entry,
    db_record,
    make_db,
    saved_db,
    task_record,
)


class ApiTest(unittest.TestCase):

    def setUp(self):
        self.app = create_app()
        self.client = self.app.test_client()

    # ─────────────────────────── Helpers ───────────────────────────

    def post(self, path, body):
        return self.client.post(path, json=body)

    def assert_ok(self, response):
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.get_json()["ok"])

    def assert_error(self, response, contains=None):
        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.get_json()["ok"])

        if contains is not None:
            self.assertIn(contains, response.get_json()["message"])

    # ─────────────────────────── Config / State ───────────────────────────

    def test_get_config_returns_calendar_url(self):
        cfg = {
            "calendars": [{"id": "calendar-id", "color": "#3366ff"}],
            "calendarTimezone": "Australia/Sydney",
        }

        with patch("server.config.load", return_value=cfg):
            res = self.client.get("/api/config")

        self.assertEqual(res.status_code, 200)
        self.assertIn("calendarUrl", res.get_json())
        self.assertIn("calendar-id", res.get_json()["calendarUrl"])
        self.assertIn("Australia/Sydney", res.get_json()["calendarUrl"])

    def test_get_state_returns_db_state(self):
        with saved_db(make_db(TASK_1, TASK_DONE, groups=[GROUP_1])):
            res = self.client.get("/api/state")

        self.assertEqual(res.status_code, 200)

        body = res.get_json()
        self.assertEqual(len(body["groups"]), 1)
        self.assertEqual(len(body["lists"]), 2)
        self.assertEqual(len(body["tasks"]), 2)
        self.assertIn("today", body)

    # ─────────────────────────── Daysheet Reads ───────────────────────────

    def test_get_daysheet_returns_entries_for_date(self):
        today_entry = daysheet_entry(
            id="entry-1",
            datetime="2026-04-26T10:30:00",
            text="Today entry",
        )
        yesterday_entry = daysheet_entry(
            id="entry-2",
            datetime="2026-04-25T09:00:00",
            text="Yesterday entry",
        )

        data = make_db(
            TASK_1,
            groups=[GROUP_1],
            lists=[{**LIST_1, "groupId": "group-1"}, LIST_2],
            daysheet=[today_entry, yesterday_entry],
        )

        with saved_db(data):
            res = self.client.get("/api/daysheet?date=2026-04-26")

        self.assertEqual(res.status_code, 200)

        body = res.get_json()
        self.assertEqual(body["date"], "2026-04-26")
        self.assertEqual(len(body["entries"]), 1)

        entry = body["entries"][0]
        self.assertEqual(entry["text"], "Today entry")
        self.assertEqual(entry["listName"], "List A")
        self.assertEqual(entry["sectionId"], "group:group-1")
        self.assertEqual(entry["sectionName"], "Group")
        self.assertTrue(entry["inGroup"])

    def test_get_daysheet_rejects_invalid_date(self):
        with saved_db(make_db()):
            res = self.client.get("/api/daysheet?date=not-a-date")

        self.assertEqual(res.status_code, 400)

    # ─────────────────────────── Task Routes ───────────────────────────

    def test_add_task(self):
        with (
            saved_db(make_db()) as saved,
            patch("server.db.new_id", return_value="task-new"),
        ):
            res = self.post("/api/add", {
                "list": "List A",
                "name": "New task",
                "due": "2026-05-01",
            })

        self.assert_ok(res)

        task = saved["tasks"][0]
        self.assertEqual(task["id"], "task-new")
        self.assertEqual(task["name"], "New task")
        self.assertEqual(task["due"], "2026-05-01")

    def test_add_task_rejects_duplicate(self):
        with saved_db(make_db(TASK_1)):
            res = self.post("/api/add", {
                "list": "List A",
                "name": "Task A",
            })

        self.assert_error(res, "already exists")

    def test_edit_task_renames_task(self):
        with saved_db(make_db(TASK_1)) as saved:
            res = self.post("/api/edit", {
                "list": "List A",
                "name": "Task A",
                "newName": "Renamed task",
            })

        self.assert_ok(res)
        self.assertEqual(saved["tasks"][0]["name"], "Renamed task")

    def test_edit_task_sets_due(self):
        with saved_db(make_db(TASK_1)) as saved:
            res = self.post("/api/edit", {
                "list": "List A",
                "name": "Task A",
                "newName": "Task A",
                "due": "2026-05-15",
            })

        self.assert_ok(res)
        self.assertEqual(saved["tasks"][0]["due"], "2026-05-15")

    def test_edit_task_clears_due(self):
        task = task_record(due="2026-05-01")

        with saved_db(make_db(task)) as saved:
            res = self.post("/api/edit", {
                "list": "List A",
                "name": "Task A",
                "newName": "Task A",
                "due": None,
            })

        self.assert_ok(res)
        self.assertIsNone(saved["tasks"][0]["due"])

    def test_edit_task_preserves_due_when_due_key_missing(self):
        task = task_record(due="2026-05-01")

        with saved_db(make_db(task)) as saved:
            res = self.post("/api/edit", {
                "list": "List A",
                "name": "Task A",
                "newName": "Renamed task",
            })

        self.assert_ok(res)
        self.assertEqual(saved["tasks"][0]["due"], "2026-05-01")

    def test_edit_task_rejects_duplicate_name(self):
        task_2 = task_record(id="task-2", name="Task B", list_id="list-1")

        with saved_db(make_db(TASK_1, task_2)):
            res = self.post("/api/edit", {
                "list": "List A",
                "name": "Task A",
                "newName": "Task B",
            })

        self.assert_error(res, "already exists")

    def test_edit_task_rejects_missing_task(self):
        with saved_db(make_db()):
            res = self.post("/api/edit", {
                "list": "List A",
                "name": "Ghost task",
                "newName": "New name",
            })

        self.assert_error(res, "not found")

    def test_delete_task(self):
        with saved_db(make_db(TASK_1)) as saved:
            res = self.post("/api/delete", {
                "list": "List A",
                "name": "Task A",
            })

        self.assert_ok(res)
        self.assertEqual(saved["tasks"], [])

    def test_delete_task_rejects_missing_task(self):
        with saved_db(make_db()):
            res = self.post("/api/delete", {
                "list": "List A",
                "name": "Ghost task",
            })

        self.assert_error(res, "not found")

    def test_move_task(self):
        with saved_db(make_db(TASK_1)) as saved:
            res = self.post("/api/move-task", {
                "list": "List A",
                "name": "Task A",
                "newList": "List B",
            })

        self.assert_ok(res)
        self.assertEqual(saved["tasks"][0]["listId"], "list-2")

    def test_move_task_rejects_duplicate_in_destination(self):
        duplicate = task_record(id="task-2", name="Task A", list_id="list-2")

        with saved_db(make_db(TASK_1, duplicate)):
            res = self.post("/api/move-task", {
                "list": "List A",
                "name": "Task A",
                "newList": "List B",
            })

        self.assert_error(res, "already exists")

    def test_done_task(self):
        with (
            saved_db(make_db(TASK_1)) as saved,
            patch("server.services.utils.date") as mock_date,
            patch("server.services.tasks.now", return_value=NOW_DT),
            patch("server.db.new_id", return_value="entry-1"),
        ):
            mock_date.today.return_value.isoformat.return_value = TODAY
            res = self.post("/api/done", {
                "list": "List A",
                "name": "Task A",
            })

        self.assert_ok(res)

        self.assertEqual(saved["tasks"][0]["done"], TODAY)
        self.assertEqual(saved["daysheet"][0]["type"], DaysheetEntryType.DONE)

    def test_done_task_rejects_already_done_task(self):
        with saved_db(make_db(TASK_DONE)):
            res = self.post("/api/done", {
                "list": "List A",
                "name": "Task B",
            })

        self.assert_error(res, "already done")

    def test_undo_task(self):
        with saved_db(make_db(TASK_DONE)) as saved:
            res = self.post("/api/undo", {
                "list": "List A",
                "name": "Task B",
            })

        self.assert_ok(res)
        self.assertIsNone(saved["tasks"][0]["done"])

    def test_task_description_updates_description(self):
        with saved_db(make_db(TASK_1)) as saved:
            res = self.post("/api/task-description", {
                "list": "List A",
                "name": "Task A",
                "description": "My notes",
            })

        self.assert_ok(res)
        self.assertEqual(saved["tasks"][0]["description"], "My notes")

    def test_task_description_rejects_missing_task(self):
        with saved_db(make_db()):
            res = self.post("/api/task-description", {
                "list": "List A",
                "name": "Ghost task",
                "description": "Notes",
            })

        self.assert_error(res, "not found")

    def test_get_state_normalizes_description(self):
        task_without_desc = {
            "id": "task-1",
            "name": "Task A",
            "listId": "list-1",
            "due": None,
            "done": None,
        }

        with saved_db(make_db(task_without_desc)):
            res = self.client.get("/api/state")

        self.assertEqual(res.status_code, 200)
        task = res.get_json()["tasks"][0]
        self.assertEqual(task["description"], "")

    # ─────────────────────────── List Routes ───────────────────────────

    def test_add_list(self):
        with (
            saved_db(make_db()) as saved,
            patch("server.db.new_id", return_value="list-new"),
        ):
            res = self.post("/api/add-list", {"list": "List C"})

        self.assert_ok(res)

        names = [lst["name"] for lst in saved["lists"]]
        self.assertIn("List C", names)

    def test_add_list_rejects_duplicate(self):
        with saved_db(make_db()):
            res = self.post("/api/add-list", {"list": "List A"})

        self.assert_error(res, "already exists")

    def test_rename_list(self):
        with saved_db(make_db()) as saved:
            res = self.post("/api/rename-list", {
                "list": "List A",
                "newName": "Renamed list",
            })

        self.assert_ok(res)

        names = [lst["name"] for lst in saved["lists"]]
        self.assertIn("Renamed list", names)
        self.assertNotIn("List A", names)

    def test_rename_list_rejects_empty_name(self):
        with saved_db(make_db()):
            res = self.post("/api/rename-list", {
                "list": "List A",
                "newName": "",
            })

        self.assert_error(res, "name is required")

    def test_delete_list(self):
        with saved_db(make_db(TASK_1)) as saved:
            res = self.post("/api/delete-list", {"list": "List A"})

        self.assert_ok(res)

        list_names = [lst["name"] for lst in saved["lists"]]
        task_list_ids = [task["listId"] for task in saved["tasks"]]

        self.assertNotIn("List A", list_names)
        self.assertNotIn("list-1", task_list_ids)

    def test_delete_list_prunes_empty_group(self):
        grouped_list = {**LIST_1, "groupId": "group-1"}

        data = make_db(
            groups=[GROUP_1],
            lists=[grouped_list],
        )

        with saved_db(data) as saved:
            res = self.post("/api/delete-list", {"list": "List A"})

        self.assert_ok(res)
        self.assertEqual(saved["groups"], [])

    def test_move_list_to_group(self):
        data = make_db(groups=[GROUP_1])

        with saved_db(data) as saved:
            res = self.post("/api/move-list", {
                "list": "List B",
                "group": "Group",
            })

        self.assert_ok(res)

        lst = next(lst for lst in saved["lists"] if lst["name"] == "List B")
        self.assertEqual(lst["groupId"], "group-1")

    def test_move_list_ungroups_list(self):
        grouped_list = {**LIST_1, "groupId": "group-1"}
        data = make_db(groups=[GROUP_1], lists=[grouped_list, LIST_2])

        with saved_db(data) as saved:
            res = self.post("/api/move-list", {
                "list": "List A",
                "group": "",
            })

        self.assert_ok(res)

        lst = next(lst for lst in saved["lists"] if lst["name"] == "List A")
        self.assertIsNone(lst["groupId"])

    # ─────────────────────────── Group Routes ───────────────────────────

    def test_rename_group(self):
        with saved_db(make_db(groups=[GROUP_1])) as saved:
            res = self.post("/api/rename-group", {
                "group": "Group",
                "newName": "Renamed group",
            })

        self.assert_ok(res)

        names = [group["name"] for group in saved["groups"]]
        self.assertIn("Renamed group", names)
        self.assertNotIn("Group", names)

    def test_rename_group_rejects_missing_group(self):
        with saved_db(make_db(groups=[GROUP_1])):
            res = self.post("/api/rename-group", {
                "group": "Missing group",
                "newName": "New group",
            })

        self.assert_error(res, "not found")

    def test_delete_group_ungroups_lists(self):
        grouped_list = {**LIST_1, "groupId": "group-1"}
        data = make_db(groups=[GROUP_1], lists=[grouped_list, LIST_2])

        with saved_db(data) as saved:
            res = self.post("/api/delete-group", {"group": "Group"})

        self.assert_ok(res)
        self.assertEqual(saved["groups"], [])

        lst = next(lst for lst in saved["lists"] if lst["id"] == "list-1")
        self.assertIsNone(lst["groupId"])

    # ─────────────────────────── Daysheet Routes ───────────────────────────

    def test_add_log_entry(self):
        with (
            saved_db(make_db(TASK_1)) as saved,
            patch("server.services.daysheet.now", return_value=NOW_DT),
            patch("server.db.new_id", return_value="entry-1"),
        ):
            res = self.post("/api/log", {
                "list": "List A",
                "text": "Talked with team",
            })

        self.assert_ok(res)

        entry = saved["daysheet"][0]
        self.assertEqual(entry["type"], DaysheetEntryType.LOG)
        self.assertEqual(entry["text"], "Talked with team")
        self.assertEqual(entry["datetime"], NOW_DT)

    def test_continue_task(self):
        with (
            saved_db(make_db(TASK_1)) as saved,
            patch("server.services.utils.date") as mock_date,
            patch("server.services.daysheet.now", return_value=NOW_DT),
            patch("server.db.new_id", return_value="entry-1"),
        ):
            mock_date.today.return_value.isoformat.return_value = TODAY
            res = self.post("/api/continue", {
                "list": "List A",
                "task": "Task A",
            })

        self.assert_ok(res)

        entry = saved["daysheet"][0]
        self.assertEqual(entry["type"], DaysheetEntryType.CONTINUE)
        self.assertEqual(entry["text"], "Task A")

    def test_continue_task_rejects_missing_task(self):
        with saved_db(make_db(TASK_1)):
            res = self.post("/api/continue", {
                "list": "List A",
                "task": "Ghost task",
            })

        self.assert_error(res, "not found")

    def test_edit_daysheet_log_entry(self):
        entry = daysheet_entry(id="entry-1", text="Old text")

        with saved_db(make_db(TASK_1, daysheet=[entry])) as saved:
            res = self.post("/api/daysheet/edit", {
                "id": "entry-1",
                "text": "New text",
            })

        self.assert_ok(res)
        self.assertEqual(saved["daysheet"][0]["text"], "New text")

    def test_edit_daysheet_rejects_non_log_entry(self):
        entry = daysheet_entry(
            id="entry-1",
            type=DaysheetEntryType.DONE,
            text="Task A",
        )

        with saved_db(make_db(TASK_1, daysheet=[entry])):
            res = self.post("/api/daysheet/edit", {
                "id": "entry-1",
                "text": "New text",
            })

        self.assert_error(res, "only log entries")

    def test_delete_daysheet_entry(self):
        entry = daysheet_entry(id="entry-1")

        with saved_db(make_db(TASK_1, daysheet=[entry])) as saved:
            res = self.post("/api/daysheet/delete", {"id": "entry-1"})

        self.assert_ok(res)
        self.assertEqual(saved["daysheet"], [])

    def test_delete_daysheet_entry_rejects_missing_entry(self):
        with saved_db(make_db(TASK_1)):
            res = self.post("/api/daysheet/delete", {"id": "missing-entry"})

        self.assert_error(res, "entry not found")


if __name__ == "__main__":
    unittest.main()
