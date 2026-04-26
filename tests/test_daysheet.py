import copy
import unittest
from unittest.mock import patch

from taskman.commands.daysheet import cmd_log, cmd_continue, cmd_daysheet

LIST_1 = {"id": "list-1", "name": "COMP3131", "groupId": None}
LIST_2 = {"id": "list-2", "name": "Work", "groupId": None}
TASK_1 = {"id": "task-1", "name": "LEC 01", "listId": "list-1", "due": None, "done": None}
TASK_DONE = {"id": "task-2", "name": "LEC 02", "listId": "list-1", "due": None, "done": "2026-04-26"}

TODAY = "2026-04-26"
NOW_DT = "2026-04-26T10:00:00"


def make_db(*daysheet_entries, tasks=None, lists=None):
    return {
        "groups": [],
        "lists": list(lists or [LIST_1, LIST_2]),
        "tasks": [copy.deepcopy(t) for t in (tasks or [TASK_1])],
        "daysheet": list(daysheet_entries),
    }


class LogTest(unittest.TestCase):

    def test_log_adds_entry(self):
        db = make_db()
        saved = {}
        with patch("taskman.db.load", return_value=db), \
             patch("taskman.db.save", side_effect=lambda d: saved.update(d)), \
             patch("taskman.db.new_id", return_value="new-id"), \
             patch("taskman.commands.daysheet._now", return_value=NOW_DT):
            cmd_log(["COMP3131", "Talked with tutor"])

        self.assertEqual(len(saved["daysheet"]), 1)
        e = saved["daysheet"][0]
        self.assertEqual(e["type"], "log")
        self.assertEqual(e["text"], "Talked with tutor")
        self.assertEqual(e["listId"], "list-1")

    def test_log_unknown_list_errors(self):
        db = make_db()
        with patch("taskman.db.load", return_value=db), patch("taskman.db.save"):
            with self.assertRaises(SystemExit):
                cmd_log(["NoSuchList", "Some text"])

    def test_log_edit_updates_text(self):
        entry = {"id": "e-1", "datetime": NOW_DT, "listId": "list-1", "type": "log", "text": "Old text"}
        db = make_db(entry)
        saved = {}
        with patch("taskman.db.load", return_value=db), \
             patch("taskman.db.save", side_effect=lambda d: saved.update(d)), \
             patch("taskman.commands.daysheet.date") as mock_date:
            mock_date.today.return_value.isoformat.return_value = TODAY
            cmd_log(["edit", "COMP3131", "Old text", "New text"])

        self.assertEqual(saved["daysheet"][0]["text"], "New text")

    def test_log_edit_not_found_errors(self):
        db = make_db()
        with patch("taskman.db.load", return_value=db), \
             patch("taskman.db.save"), \
             patch("taskman.commands.daysheet.date") as mock_date:
            mock_date.today.return_value.isoformat.return_value = TODAY
            with self.assertRaises(SystemExit):
                cmd_log(["edit", "COMP3131", "Ghost", "New text"])

    def test_log_delete_removes_entry(self):
        entry = {"id": "e-1", "datetime": NOW_DT, "listId": "list-1", "type": "log", "text": "Some text"}
        db = make_db(entry)
        saved = {}
        with patch("taskman.db.load", return_value=db), \
             patch("taskman.db.save", side_effect=lambda d: saved.update(d)), \
             patch("taskman.commands.daysheet.date") as mock_date:
            mock_date.today.return_value.isoformat.return_value = TODAY
            cmd_log(["delete", "COMP3131", "Some text"])

        self.assertEqual(len(saved["daysheet"]), 0)

    def test_log_delete_not_found_errors(self):
        db = make_db()
        with patch("taskman.db.load", return_value=db), \
             patch("taskman.db.save"), \
             patch("taskman.commands.daysheet.date") as mock_date:
            mock_date.today.return_value.isoformat.return_value = TODAY
            with self.assertRaises(SystemExit):
                cmd_log(["delete", "COMP3131", "Ghost"])


class ContinueTest(unittest.TestCase):

    def test_continue_adds_entry(self):
        db = make_db()
        saved = {}
        with patch("taskman.db.load", return_value=db), \
             patch("taskman.db.save", side_effect=lambda d: saved.update(d)), \
             patch("taskman.db.new_id", return_value="new-id"), \
             patch("taskman.commands.daysheet._now", return_value=NOW_DT), \
             patch("taskman.commands.daysheet.date") as mock_date:
            mock_date.today.return_value.isoformat.return_value = TODAY
            cmd_continue(["COMP3131", "LEC 01"])

        self.assertEqual(len(saved["daysheet"]), 1)
        e = saved["daysheet"][0]
        self.assertEqual(e["type"], "continue")
        self.assertEqual(e["text"], "LEC 01")

    def test_continue_requires_task_to_exist(self):
        db = make_db()
        with patch("taskman.db.load", return_value=db), patch("taskman.db.save"):
            with self.assertRaises(SystemExit):
                cmd_continue(["COMP3131", "Ghost task"])

    def test_continue_blocked_if_done_today(self):
        done_entry = {"id": "e-1", "datetime": NOW_DT, "listId": "list-1", "type": "done", "text": "LEC 01"}
        db = make_db(done_entry)
        with patch("taskman.db.load", return_value=db), \
             patch("taskman.db.save"), \
             patch("taskman.commands.daysheet.date") as mock_date:
            mock_date.today.return_value.isoformat.return_value = TODAY
            with self.assertRaises(SystemExit):
                cmd_continue(["COMP3131", "LEC 01"])


class DoneWritesDaysheetTest(unittest.TestCase):

    def test_done_adds_daysheet_entry(self):
        from taskman.commands.tasks import cmd_done
        db = {
            "groups": [], "lists": [LIST_1], "tasks": [copy.deepcopy(TASK_1)], "daysheet": [],
        }
        saved = {}
        with patch("taskman.db.load", return_value=db), \
             patch("taskman.db.save", side_effect=lambda d: saved.update(d)), \
             patch("taskman.db.new_id", return_value="new-id"), \
             patch("taskman.commands.tasks.date") as mock_date, \
             patch("taskman.commands.tasks.datetime") as mock_dt, \
             patch("taskman.commands.tasks._play_sound"):
            mock_date.today.return_value.isoformat.return_value = TODAY
            mock_dt.now.return_value.strftime.return_value = NOW_DT
            cmd_done(["COMP3131", "LEC 01"])

        self.assertEqual(len(saved["daysheet"]), 1)
        e = saved["daysheet"][0]
        self.assertEqual(e["type"], "done")
        self.assertEqual(e["text"], "LEC 01")

    def test_done_removes_continue_entry(self):
        from taskman.commands.tasks import cmd_done
        cont_entry = {"id": "e-1", "datetime": NOW_DT, "listId": "list-1", "type": "continue", "text": "LEC 01"}
        db = {
            "groups": [], "lists": [LIST_1], "tasks": [copy.deepcopy(TASK_1)], "daysheet": [cont_entry],
        }
        saved = {}
        with patch("taskman.db.load", return_value=db), \
             patch("taskman.db.save", side_effect=lambda d: saved.update(d)), \
             patch("taskman.db.new_id", return_value="new-id"), \
             patch("taskman.commands.tasks.date") as mock_date, \
             patch("taskman.commands.tasks.datetime") as mock_dt, \
             patch("taskman.commands.tasks._play_sound"):
            mock_date.today.return_value.isoformat.return_value = TODAY
            mock_dt.now.return_value.strftime.return_value = NOW_DT
            cmd_done(["COMP3131", "LEC 01"])

        types = [e["type"] for e in saved["daysheet"]]
        self.assertNotIn("continue", types)
        self.assertIn("done", types)


class DaysheetViewTest(unittest.TestCase):

    def test_daysheet_no_entries(self, ):
        db = make_db()
        with patch("taskman.db.load", return_value=db):
            from io import StringIO
            import sys as _sys
            buf = StringIO()
            _sys.stdout = buf
            try:
                cmd_daysheet(["2026-04-26"])
            finally:
                _sys.stdout = _sys.__stdout__
        self.assertIn("No entries", buf.getvalue())

    def test_daysheet_shows_entries(self):
        entries = [
            {"id": "e-1", "datetime": "2026-04-26T09:00:00", "listId": "list-1", "type": "done", "text": "LEC 01"},
            {"id": "e-2", "datetime": "2026-04-26T10:00:00", "listId": "list-1", "type": "continue", "text": "LEC 02"},
            {"id": "e-3", "datetime": "2026-04-26T11:00:00", "listId": "list-1", "type": "log", "text": "Asked tutor"},
        ]
        db = make_db(*entries)
        with patch("taskman.db.load", return_value=db):
            from io import StringIO
            import sys as _sys
            buf = StringIO()
            _sys.stdout = buf
            try:
                cmd_daysheet(["2026-04-26"])
            finally:
                _sys.stdout = _sys.__stdout__
        out = buf.getvalue()
        self.assertIn("Finished LEC 01", out)
        self.assertIn("Continued LEC 02", out)
        self.assertIn("Asked tutor", out)

    def test_daysheet_filters_by_date(self):
        entries = [
            {"id": "e-1", "datetime": "2026-04-25T09:00:00", "listId": "list-1", "type": "done", "text": "LEC 01"},
            {"id": "e-2", "datetime": "2026-04-26T09:00:00", "listId": "list-1", "type": "done", "text": "LEC 02"},
        ]
        db = make_db(*entries)
        with patch("taskman.db.load", return_value=db):
            from io import StringIO
            import sys as _sys
            buf = StringIO()
            _sys.stdout = buf
            try:
                cmd_daysheet(["2026-04-26"])
            finally:
                _sys.stdout = _sys.__stdout__
        out = buf.getvalue()
        self.assertNotIn("LEC 01", out)
        self.assertIn("LEC 02", out)


if __name__ == "__main__":
    unittest.main()
