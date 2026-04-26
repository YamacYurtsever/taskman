import copy
import unittest
from unittest.mock import patch

from taskman.commands.tasks import (
    cmd_add, cmd_del, cmd_done, cmd_move, cmd_undo, cmd_update,
)

LIST_1 = {"id": "list-1", "name": "Work", "groupId": None}
LIST_2 = {"id": "list-2", "name": "Personal", "groupId": None}
TASK_1 = {"id": "task-1", "name": "Write report", "listId": "list-1", "due": None, "done": None}
TASK_DONE = {"id": "task-2", "name": "Done task", "listId": "list-1", "due": None, "done": "2026-04-25"}


def make_db(*tasks, lists=None):
    return {
        "groups": [],
        "lists": list(lists or [LIST_1, LIST_2]),
        "tasks": [copy.deepcopy(t) for t in tasks],
        "daysheet": [],
    }


class TasksTest(unittest.TestCase):

    # --- add ---

    def test_add_creates_task(self):
        db = make_db()
        saved = {}
        with patch("taskman.db.load", return_value=db), \
             patch("taskman.db.save", side_effect=lambda d: saved.update(d)), \
             patch("taskman.db.new_id", return_value="new-id"):
            cmd_add(["Work", "New task"])

        self.assertEqual(len(saved["tasks"]), 1)
        task = saved["tasks"][0]
        self.assertEqual(task["name"], "New task")
        self.assertEqual(task["listId"], "list-1")
        self.assertIsNone(task["due"])
        self.assertIsNone(task["done"])

    def test_add_with_due_date(self):
        db = make_db()
        saved = {}
        with patch("taskman.db.load", return_value=db), \
             patch("taskman.db.save", side_effect=lambda d: saved.update(d)), \
             patch("taskman.db.new_id", return_value="new-id"):
            cmd_add(["Work", "New task", "2026-05-01"])

        self.assertEqual(saved["tasks"][0]["due"], "2026-05-01")

    def test_add_autocreates_list(self):
        db = make_db(lists=[LIST_1])
        saved = {}
        with patch("taskman.db.load", return_value=db), \
             patch("taskman.db.save", side_effect=lambda d: saved.update(d)), \
             patch("taskman.db.new_id", return_value="new-id"):
            cmd_add(["BrandNewList", "Some task"])

        list_names = [l["name"] for l in saved["lists"]]
        self.assertIn("BrandNewList", list_names)

    def test_add_duplicate_errors(self):
        db = make_db(TASK_1)
        with patch("taskman.db.load", return_value=db), \
             patch("taskman.db.save"):
            with self.assertRaises(SystemExit):
                cmd_add(["Work", "Write report"])

    def test_add_invalid_date_errors(self):
        db = make_db()
        with patch("taskman.db.load", return_value=db), \
             patch("taskman.db.save"):
            with self.assertRaises(SystemExit):
                cmd_add(["Work", "Task", "not-a-date"])

    # --- done ---

    def test_done_stamps_today(self):
        db = make_db(TASK_1)
        saved = {}
        with patch("taskman.db.load", return_value=db), \
             patch("taskman.db.save", side_effect=lambda d: saved.update(d)), \
             patch("taskman.commands.tasks.date") as mock_date:
            mock_date.today.return_value.isoformat.return_value = "2026-04-26"
            cmd_done(["Work", "Write report"])

        self.assertEqual(saved["tasks"][0]["done"], "2026-04-26")

    def test_done_unknown_list_errors(self):
        db = make_db(TASK_1)
        with patch("taskman.db.load", return_value=db), \
             patch("taskman.db.save"):
            with self.assertRaises(SystemExit):
                cmd_done(["NoSuchList", "Write report"])

    def test_done_unknown_task_errors(self):
        db = make_db()
        with patch("taskman.db.load", return_value=db), \
             patch("taskman.db.save"):
            with self.assertRaises(SystemExit):
                cmd_done(["Work", "No such task"])

    def test_done_already_done_errors(self):
        db = make_db(TASK_DONE)
        with patch("taskman.db.load", return_value=db), \
             patch("taskman.db.save"):
            with self.assertRaises(SystemExit):
                cmd_done(["Work", "Done task"])

    # --- undo ---

    def test_undo_clears_done(self):
        db = make_db(TASK_DONE)
        saved = {}
        with patch("taskman.db.load", return_value=db), \
             patch("taskman.db.save", side_effect=lambda d: saved.update(d)):
            cmd_undo(["Work", "Done task"])

        self.assertIsNone(saved["tasks"][0]["done"])

    def test_undo_on_pending_errors(self):
        db = make_db(TASK_1)
        with patch("taskman.db.load", return_value=db), \
             patch("taskman.db.save"):
            with self.assertRaises(SystemExit):
                cmd_undo(["Work", "Write report"])

    # --- update ---

    def test_update_renames(self):
        db = make_db(TASK_1)
        saved = {}
        with patch("taskman.db.load", return_value=db), \
             patch("taskman.db.save", side_effect=lambda d: saved.update(d)):
            cmd_update(["Work", "Write report", "Write final report"])

        self.assertEqual(saved["tasks"][0]["name"], "Write final report")

    def test_update_changes_due(self):
        db = make_db(TASK_1)
        saved = {}
        with patch("taskman.db.load", return_value=db), \
             patch("taskman.db.save", side_effect=lambda d: saved.update(d)):
            cmd_update(["Work", "Write report", "Write report", "2026-06-01"])

        self.assertEqual(saved["tasks"][0]["due"], "2026-06-01")

    def test_update_omitting_date_preserves_due(self):
        task = {**TASK_1, "due": "2026-05-01"}
        db = make_db(task)
        saved = {}
        with patch("taskman.db.load", return_value=db), \
             patch("taskman.db.save", side_effect=lambda d: saved.update(d)):
            cmd_update(["Work", "Write report", "Renamed"])

        self.assertEqual(saved["tasks"][0]["due"], "2026-05-01")

    def test_update_unknown_task_errors(self):
        db = make_db()
        with patch("taskman.db.load", return_value=db), \
             patch("taskman.db.save"):
            with self.assertRaises(SystemExit):
                cmd_update(["Work", "Ghost", "New name"])

    # --- move ---

    def test_move_changes_list(self):
        db = make_db(TASK_1)
        saved = {}
        with patch("taskman.db.load", return_value=db), \
             patch("taskman.db.save", side_effect=lambda d: saved.update(d)), \
             patch("taskman.db.new_id", return_value="new-id"):
            cmd_move(["Work", "Write report", "Personal"])

        self.assertEqual(saved["tasks"][0]["listId"], "list-2")

    def test_move_autocreates_dest_list(self):
        db = make_db(TASK_1, lists=[LIST_1])
        saved = {}
        with patch("taskman.db.load", return_value=db), \
             patch("taskman.db.save", side_effect=lambda d: saved.update(d)), \
             patch("taskman.db.new_id", return_value="new-id"):
            cmd_move(["Work", "Write report", "NewList"])

        list_names = [l["name"] for l in saved["lists"]]
        self.assertIn("NewList", list_names)

    def test_move_unknown_task_errors(self):
        db = make_db()
        with patch("taskman.db.load", return_value=db), \
             patch("taskman.db.save"):
            with self.assertRaises(SystemExit):
                cmd_move(["Work", "Ghost", "Personal"])

    # --- del ---

    def test_del_removes_task(self):
        db = make_db(TASK_1)
        saved = {}
        with patch("taskman.db.load", return_value=db), \
             patch("taskman.db.save", side_effect=lambda d: saved.update(d)):
            cmd_del(["Work", "Write report"])

        self.assertEqual(len(saved["tasks"]), 0)

    def test_del_unknown_task_errors(self):
        db = make_db()
        with patch("taskman.db.load", return_value=db), \
             patch("taskman.db.save"):
            with self.assertRaises(SystemExit):
                cmd_del(["Work", "Ghost"])


if __name__ == "__main__":
    unittest.main()
