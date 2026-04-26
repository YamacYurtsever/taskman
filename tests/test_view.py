import unittest
from datetime import date
from unittest.mock import patch

from taskman.commands.view import cmd_ls, filter_tasks

TODAY = date(2026, 4, 26)

LIST_1 = {"id": "list-1", "name": "Work", "groupId": None}
LIST_2 = {"id": "list-2", "name": "Personal", "groupId": "group-1"}
LIST_3 = {"id": "list-3", "name": "Side", "groupId": "group-1"}
GROUP_1 = {"id": "group-1", "name": "Mine"}

TASK_OVERDUE    = {"id": "t1", "name": "Overdue task",  "listId": "list-1", "due": "2026-04-20", "done": None}
TASK_TODAY      = {"id": "t2", "name": "Today task",    "listId": "list-1", "due": "2026-04-26", "done": None}
TASK_TOMORROW   = {"id": "t3", "name": "Tomorrow task", "listId": "list-1", "due": "2026-04-27", "done": None}
TASK_NEXT_WEEK  = {"id": "t4", "name": "Next week",     "listId": "list-1", "due": "2026-05-10", "done": None}
TASK_DATELESS   = {"id": "t5", "name": "No due date",   "listId": "list-1", "due": None,         "done": None}
TASK_DONE       = {"id": "t6", "name": "Done task",     "listId": "list-1", "due": "2026-04-26", "done": "2026-04-25"}


class FilterTasksTest(unittest.TestCase):

    def _tasks(self):
        return [TASK_OVERDUE, TASK_TODAY, TASK_TOMORROW, TASK_NEXT_WEEK, TASK_DATELESS, TASK_DONE]

    # --- default mode ---

    def test_default_excludes_done(self):
        result = filter_tasks(self._tasks(), "list-1", "all", TODAY)
        names = [t["name"] for t in result]
        self.assertNotIn("Done task", names)

    def test_default_dated_before_dateless(self):
        result = filter_tasks(self._tasks(), "list-1", "all", TODAY)
        names = [t["name"] for t in result]
        dateless_idx = names.index("No due date")
        for t in result[:dateless_idx]:
            self.assertIsNotNone(t["due"])

    def test_default_dated_sorted_by_due(self):
        result = filter_tasks(self._tasks(), "list-1", "all", TODAY)
        dated = [t for t in result if t["due"]]
        dues = [t["due"] for t in dated]
        self.assertEqual(dues, sorted(dues))

    def test_default_includes_dateless(self):
        result = filter_tasks(self._tasks(), "list-1", "all", TODAY)
        names = [t["name"] for t in result]
        self.assertIn("No due date", names)

    # --- today mode ---

    def test_today_includes_overdue(self):
        result = filter_tasks(self._tasks(), "list-1", "day", TODAY)
        names = [t["name"] for t in result]
        self.assertIn("Overdue task", names)

    def test_today_includes_due_today(self):
        result = filter_tasks(self._tasks(), "list-1", "day", TODAY)
        names = [t["name"] for t in result]
        self.assertIn("Today task", names)

    def test_today_excludes_future(self):
        result = filter_tasks(self._tasks(), "list-1", "day", TODAY)
        names = [t["name"] for t in result]
        self.assertNotIn("Tomorrow task", names)
        self.assertNotIn("Next week", names)

    def test_today_excludes_dateless(self):
        result = filter_tasks(self._tasks(), "list-1", "day", TODAY)
        names = [t["name"] for t in result]
        self.assertNotIn("No due date", names)

    def test_today_excludes_done(self):
        result = filter_tasks(self._tasks(), "list-1", "day", TODAY)
        names = [t["name"] for t in result]
        self.assertNotIn("Done task", names)

    # --- week mode ---

    def test_week_includes_overdue(self):
        result = filter_tasks(self._tasks(), "list-1", "week", TODAY)
        names = [t["name"] for t in result]
        self.assertIn("Overdue task", names)

    def test_week_includes_within_7_days(self):
        result = filter_tasks(self._tasks(), "list-1", "week", TODAY)
        names = [t["name"] for t in result]
        self.assertIn("Tomorrow task", names)

    def test_week_excludes_beyond_7_days(self):
        result = filter_tasks(self._tasks(), "list-1", "week", TODAY)
        names = [t["name"] for t in result]
        self.assertNotIn("Next week", names)

    def test_week_excludes_dateless(self):
        result = filter_tasks(self._tasks(), "list-1", "week", TODAY)
        names = [t["name"] for t in result]
        self.assertNotIn("No due date", names)


class CmdLsTest(unittest.TestCase):

    TASK_PERSONAL = {"id": "t-p", "name": "Personal task", "listId": "list-2", "due": None, "done": None}
    TASK_SIDE     = {"id": "t-s", "name": "Side task",     "listId": "list-3", "due": None, "done": None}

    def _make_db(self):
        return {
            "groups": [GROUP_1],
            "lists": [LIST_1, LIST_2, LIST_3],
            "tasks": [TASK_TODAY, TASK_DATELESS, self.TASK_PERSONAL, self.TASK_SIDE],
            "daysheet": [],
        }

    def test_unknown_filter_errors(self):
        with patch("taskman.db.load", return_value=self._make_db()):
            with self.assertRaises(SystemExit):
                cmd_ls(["NonExistent"])

    def test_list_filter(self, ):
        printed = []
        with patch("taskman.db.load", return_value=self._make_db()), \
             patch("builtins.print", side_effect=lambda *a, **k: printed.append(a)):
            cmd_ls(["Work"])
        output = " ".join(str(a) for line in printed for a in line)
        self.assertIn("Work", output)
        self.assertNotIn("Personal", output)

    def test_group_filter(self):
        printed = []
        with patch("taskman.db.load", return_value=self._make_db()), \
             patch("builtins.print", side_effect=lambda *a, **k: printed.append(a)):
            cmd_ls(["Mine"])
        output = " ".join(str(a) for line in printed for a in line)
        self.assertIn("Personal", output)
        self.assertIn("Side", output)
        self.assertNotIn("Work", output)

    def test_empty_list_hidden(self):
        db = {
            "groups": [],
            "lists": [LIST_1, LIST_2],
            "tasks": [TASK_DATELESS],  # only Work has a task
            "daysheet": [],
        }
        printed = []
        with patch("taskman.db.load", return_value=db), \
             patch("builtins.print", side_effect=lambda *a, **k: printed.append(a)):
            cmd_ls([])
        output = " ".join(str(a) for line in printed for a in line)
        self.assertIn("Work", output)
        self.assertNotIn("Personal", output)

    def test_empty_db_prints_message(self):
        empty = {"groups": [], "lists": [], "tasks": [], "daysheet": []}
        printed = []
        with patch("taskman.db.load", return_value=empty), \
             patch("builtins.print", side_effect=lambda *a, **k: printed.append(a)):
            cmd_ls([])
        output = " ".join(str(a) for line in printed for a in line)
        self.assertIn("no lists", output)


if __name__ == "__main__":
    unittest.main()
