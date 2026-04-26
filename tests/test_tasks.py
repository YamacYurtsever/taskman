import copy
import unittest
from unittest.mock import patch

from taskman.commands.tasks import (
    cmd_add, cmd_delete, cmd_done, cmd_edit, cmd_move, cmd_undo,
)

LIST_1 = {"id": "list-1", "name": "Work", "groupId": None}
LIST_2 = {"id": "list-2", "name": "Personal", "groupId": None}
TASK_1 = {"id": "task-1", "name": "Write report", "listId": "list-1", "due": None, "done": None}
TASK_DONE = {"id": "task-2", "name": "Done task", "listId": "list-1", "due": None, "done": "2026-04-25"}


def make_db(*tasks, lists=None):
    return {
        "groups": [],
        "lists": [copy.deepcopy(l) for l in (lists or [LIST_1, LIST_2])],
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

    def test_add_list_only(self):
        db = make_db()
        saved = {}
        with patch("taskman.db.load", return_value=db), \
             patch("taskman.db.save", side_effect=lambda d: saved.update(d)), \
             patch("taskman.db.new_id", return_value="new-id"):
            cmd_add(["NewList"])

        list_names = [l["name"] for l in saved["lists"]]
        self.assertIn("NewList", list_names)
        self.assertEqual(len(saved["tasks"]), 0)

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

    # --- edit ---

    def test_edit_renames(self):
        db = make_db(TASK_1)
        saved = {}
        with patch("taskman.db.load", return_value=db), \
             patch("taskman.db.save", side_effect=lambda d: saved.update(d)):
            cmd_edit(["Work", "Write report", "Write final report"])

        self.assertEqual(saved["tasks"][0]["name"], "Write final report")

    def test_edit_changes_due(self):
        db = make_db(TASK_1)
        saved = {}
        with patch("taskman.db.load", return_value=db), \
             patch("taskman.db.save", side_effect=lambda d: saved.update(d)):
            cmd_edit(["Work", "Write report", "Write report", "2026-06-01"])

        self.assertEqual(saved["tasks"][0]["due"], "2026-06-01")

    def test_edit_omitting_date_preserves_due(self):
        task = {**TASK_1, "due": "2026-05-01"}
        db = make_db(task)
        saved = {}
        with patch("taskman.db.load", return_value=db), \
             patch("taskman.db.save", side_effect=lambda d: saved.update(d)):
            cmd_edit(["Work", "Write report", "Renamed"])

        self.assertEqual(saved["tasks"][0]["due"], "2026-05-01")

    def test_edit_unknown_task_errors(self):
        db = make_db()
        with patch("taskman.db.load", return_value=db), \
             patch("taskman.db.save"):
            with self.assertRaises(SystemExit):
                cmd_edit(["Work", "Ghost", "New name"])

    def test_edit_renames_list(self):
        db = make_db(TASK_1)
        saved = {}
        with patch("taskman.db.load", return_value=db), \
             patch("taskman.db.save", side_effect=lambda d: saved.update(d)):
            cmd_edit(["Work", "Career"])

        list_names = [l["name"] for l in saved["lists"]]
        self.assertIn("Career", list_names)
        self.assertNotIn("Work", list_names)

    def test_edit_renames_group(self):
        group = {"id": "group-1", "name": "MyGroup"}
        data = {
            "groups": [group],
            "lists": [LIST_1, LIST_2],
            "tasks": [],
            "daysheet": [],
        }
        saved = {}
        with patch("taskman.db.load", return_value=data), \
             patch("taskman.db.save", side_effect=lambda d: saved.update(d)):
            cmd_edit(["MyGroup", "NewGroup"])

        self.assertEqual(saved["groups"][0]["name"], "NewGroup")

    def test_edit_rename_list_unknown_errors(self):
        db = make_db()
        with patch("taskman.db.load", return_value=db), \
             patch("taskman.db.save"):
            with self.assertRaises(SystemExit):
                cmd_edit(["NoSuchList", "NewName"])

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

    def test_move_list_to_group(self):
        group = {"id": "group-1", "name": "MyGroup"}
        data = {
            "groups": [group],
            "lists": [LIST_1, LIST_2],
            "tasks": [],
            "daysheet": [],
        }
        saved = {}
        with patch("taskman.db.load", return_value=data), \
             patch("taskman.db.save", side_effect=lambda d: saved.update(d)), \
             patch("taskman.db.new_id", return_value="new-id"):
            cmd_move(["Work", "MyGroup"])

        work = next(l for l in saved["lists"] if l["name"] == "Work")
        self.assertEqual(work["groupId"], "group-1")

    def test_move_list_autocreates_group(self):
        db = make_db(lists=[LIST_1, LIST_2])
        saved = {}
        with patch("taskman.db.load", return_value=db), \
             patch("taskman.db.save", side_effect=lambda d: saved.update(d)), \
             patch("taskman.db.new_id", return_value="new-id"):
            cmd_move(["Work", "BrandNewGroup"])

        self.assertEqual(len(saved["groups"]), 1)
        self.assertEqual(saved["groups"][0]["name"], "BrandNewGroup")
        work = next(l for l in saved["lists"] if l["name"] == "Work")
        self.assertEqual(work["groupId"], "new-id")

    def test_move_list_ungroup(self):
        group = {"id": "group-1", "name": "MyGroup"}
        lst = {**LIST_1, "groupId": "group-1"}
        data = {
            "groups": [group],
            "lists": [lst, LIST_2],
            "tasks": [],
            "daysheet": [],
        }
        saved = {}
        with patch("taskman.db.load", return_value=data), \
             patch("taskman.db.save", side_effect=lambda d: saved.update(d)):
            cmd_move(["Work", ""])

        work = next(l for l in saved["lists"] if l["name"] == "Work")
        self.assertIsNone(work["groupId"])

    def test_move_list_ungroup_removes_empty_group(self):
        group = {"id": "group-1", "name": "MyGroup"}
        lst = {**LIST_1, "groupId": "group-1"}
        data = {
            "groups": [group],
            "lists": [lst, LIST_2],
            "tasks": [],
            "daysheet": [],
        }
        saved = {}
        with patch("taskman.db.load", return_value=data), \
             patch("taskman.db.save", side_effect=lambda d: saved.update(d)):
            cmd_move(["Work", ""])

        self.assertEqual(len(saved["groups"]), 0)

    def test_move_list_unknown_list_errors(self):
        db = make_db()
        with patch("taskman.db.load", return_value=db), \
             patch("taskman.db.save"):
            with self.assertRaises(SystemExit):
                cmd_move(["NoSuchList", "MyGroup"])

    # --- del ---

    def test_del_removes_task(self):
        db = make_db(TASK_1)
        saved = {}
        with patch("taskman.db.load", return_value=db), \
             patch("taskman.db.save", side_effect=lambda d: saved.update(d)):
            cmd_delete(["Work", "Write report"])

        self.assertEqual(len(saved["tasks"]), 0)

    def test_del_unknown_task_errors(self):
        db = make_db()
        with patch("taskman.db.load", return_value=db), \
             patch("taskman.db.save"):
            with self.assertRaises(SystemExit):
                cmd_delete(["Work", "Ghost"])

    def test_del_list_removes_list_and_tasks(self):
        db = make_db(TASK_1)
        saved = {}
        with patch("taskman.db.load", return_value=db), \
             patch("taskman.db.save", side_effect=lambda d: saved.update(d)):
            cmd_delete(["Work"])

        list_names = [l["name"] for l in saved["lists"]]
        self.assertNotIn("Work", list_names)
        self.assertEqual(len(saved["tasks"]), 0)

    def test_del_list_keeps_other_lists(self):
        db = make_db(TASK_1)
        saved = {}
        with patch("taskman.db.load", return_value=db), \
             patch("taskman.db.save", side_effect=lambda d: saved.update(d)):
            cmd_delete(["Work"])

        list_names = [l["name"] for l in saved["lists"]]
        self.assertIn("Personal", list_names)

    def test_del_group_ungroups_lists(self):
        group = {"id": "group-1", "name": "MyGroup"}
        lst = {**LIST_1, "groupId": "group-1"}
        data = {
            "groups": [group],
            "lists": [lst, LIST_2],
            "tasks": [],
            "daysheet": [],
        }
        saved = {}
        with patch("taskman.db.load", return_value=data), \
             patch("taskman.db.save", side_effect=lambda d: saved.update(d)):
            cmd_delete(["MyGroup"])

        self.assertEqual(len(saved["groups"]), 0)
        self.assertIsNone(saved["lists"][0]["groupId"])
        self.assertEqual(len(saved["lists"]), 2)

    def test_del_group_prefers_group_over_list_same_name(self):
        group = {"id": "group-1", "name": "Work"}
        lst_grouped = {**LIST_1, "groupId": "group-1"}
        data = {
            "groups": [group],
            "lists": [lst_grouped, LIST_2],
            "tasks": [],
            "daysheet": [],
        }
        saved = {}
        with patch("taskman.db.load", return_value=data), \
             patch("taskman.db.save", side_effect=lambda d: saved.update(d)):
            cmd_delete(["Work"])

        self.assertEqual(len(saved["groups"]), 0)
        self.assertEqual(len(saved["lists"]), 2)

    def test_del_list_removes_empty_group(self):
        group = {"id": "group-1", "name": "MyGroup"}
        lst = {**LIST_1, "groupId": "group-1"}
        data = {
            "groups": [group],
            "lists": [lst, LIST_2],
            "tasks": [],
            "daysheet": [],
        }
        saved = {}
        with patch("taskman.db.load", return_value=data), \
             patch("taskman.db.save", side_effect=lambda d: saved.update(d)):
            cmd_delete(["Work"])

        self.assertEqual(len(saved["groups"]), 0)

    def test_del_list_keeps_group_if_other_lists_remain(self):
        group = {"id": "group-1", "name": "MyGroup"}
        lst1 = {**LIST_1, "groupId": "group-1"}
        lst2 = {**LIST_2, "groupId": "group-1"}
        data = {
            "groups": [group],
            "lists": [lst1, lst2],
            "tasks": [],
            "daysheet": [],
        }
        saved = {}
        with patch("taskman.db.load", return_value=data), \
             patch("taskman.db.save", side_effect=lambda d: saved.update(d)):
            cmd_delete(["Work"])

        self.assertEqual(len(saved["groups"]), 1)

    def test_del_unknown_list_errors(self):
        db = make_db()
        with patch("taskman.db.load", return_value=db), \
             patch("taskman.db.save"):
            with self.assertRaises(SystemExit):
                cmd_delete(["NoSuchList"])


if __name__ == "__main__":
    unittest.main()
