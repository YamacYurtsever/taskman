import copy
import unittest
from unittest.mock import patch

from web.server import create_app


LIST_1 = {"id": "list-1", "name": "Work", "groupId": "group-1"}
LIST_2 = {"id": "list-2", "name": "Personal", "groupId": None}
GROUP_1 = {"id": "group-1", "name": "UNSW"}
TASK_1 = {"id": "task-1", "name": "Write report", "listId": "list-1", "due": None, "done": None}
TASK_DONE = {"id": "task-2", "name": "Done task", "listId": "list-1", "due": None, "done": "2026-04-25"}


def make_db():
    return {
        "groups": [copy.deepcopy(GROUP_1)],
        "lists": [copy.deepcopy(LIST_1), copy.deepcopy(LIST_2)],
        "tasks": [copy.deepcopy(TASK_1), copy.deepcopy(TASK_DONE)],
        "daysheet": [],
    }


class WebTest(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.client = self.app.test_client()
        self.saved = {}

    def _patches(self, data):
        self.saved.clear()
        return (
            patch("taskman.db.load", return_value=data),
            patch("taskman.db.save", side_effect=lambda d: self.saved.update(d)),
        )

    def _patch_all(self, data):
        load_p, save_p = self._patches(data)
        load_p.start(); save_p.start()
        self.addCleanup(load_p.stop); self.addCleanup(save_p.stop)

    # --- GET /api/state ---

    def test_get_state(self):
        self._patch_all(make_db())
        res = self.client.get("/api/state")
        self.assertEqual(res.status_code, 200)
        body = res.get_json()
        self.assertEqual(len(body["lists"]), 2)
        self.assertEqual(len(body["tasks"]), 2)
        self.assertEqual(len(body["groups"]), 1)
        self.assertIn("today", body)

    # --- GET /api/daysheet ---

    def test_get_daysheet(self):
        data = make_db()
        data["daysheet"].append({
            "id": "e1", "datetime": "2026-04-26T10:30:00",
            "listId": "list-1", "type": "log", "text": "hello",
        })
        data["daysheet"].append({
            "id": "e2", "datetime": "2026-04-25T09:00:00",
            "listId": "list-1", "type": "log", "text": "yesterday",
        })
        self._patch_all(data)
        res = self.client.get("/api/daysheet?date=2026-04-26")
        self.assertEqual(res.status_code, 200)
        body = res.get_json()
        self.assertEqual(body["date"], "2026-04-26")
        self.assertEqual(len(body["entries"]), 1)
        self.assertEqual(body["entries"][0]["text"], "hello")
        self.assertEqual(body["entries"][0]["listName"], "Work")

    def test_get_daysheet_invalid_date(self):
        self._patch_all(make_db())
        res = self.client.get("/api/daysheet?date=not-a-date")
        self.assertEqual(res.status_code, 400)

    # --- POST /api/add ---

    def test_add_task(self):
        self._patch_all(make_db())
        res = self.client.post("/api/add", json={"list": "Work", "name": "New thing", "due": "2026-05-01"})
        self.assertEqual(res.status_code, 200)
        self.assertTrue(res.get_json()["ok"])
        names = [t["name"] for t in self.saved["tasks"]]
        self.assertIn("New thing", names)

    def test_add_duplicate_returns_400(self):
        self._patch_all(make_db())
        res = self.client.post("/api/add", json={"list": "Work", "name": "Write report"})
        self.assertEqual(res.status_code, 400)
        self.assertFalse(res.get_json()["ok"])
        self.assertIn("already exists", res.get_json()["message"])

    # --- POST /api/done & /api/undo ---

    def test_done_task(self):
        self._patch_all(make_db())
        with patch("taskman.commands.tasks._play_sound"):
            res = self.client.post("/api/done", json={"list": "Work", "name": "Write report"})
        self.assertEqual(res.status_code, 200)
        task = next(t for t in self.saved["tasks"] if t["name"] == "Write report")
        self.assertIsNotNone(task["done"])

    def test_undo_task(self):
        self._patch_all(make_db())
        res = self.client.post("/api/undo", json={"list": "Work", "name": "Done task"})
        self.assertEqual(res.status_code, 200)
        task = next(t for t in self.saved["tasks"] if t["name"] == "Done task")
        self.assertIsNone(task["done"])

    # --- POST /api/delete ---

    def test_delete_task(self):
        self._patch_all(make_db())
        res = self.client.post("/api/delete", json={"list": "Work", "name": "Write report"})
        self.assertEqual(res.status_code, 200)
        names = [t["name"] for t in self.saved["tasks"]]
        self.assertNotIn("Write report", names)

    def test_delete_missing_returns_400(self):
        self._patch_all(make_db())
        res = self.client.post("/api/delete", json={"list": "Work", "name": "nope"})
        self.assertEqual(res.status_code, 400)

    # --- POST /api/log ---

    def test_log_entry(self):
        self._patch_all(make_db())
        res = self.client.post("/api/log", json={"list": "Work", "text": "talked with team"})
        self.assertEqual(res.status_code, 200)
        self.assertEqual(len(self.saved["daysheet"]), 1)
        entry = self.saved["daysheet"][0]
        self.assertEqual(entry["type"], "log")
        self.assertEqual(entry["text"], "talked with team")

    # --- POST /api/daysheet/delete ---

    def test_daysheet_delete_entry(self):
        db = make_db()
        db["daysheet"] = [{"id": "e-1", "datetime": "2026-04-26T10:00:00", "listId": "list-1", "type": "log", "text": "talked with team"}]
        self._patch_all(db)
        res = self.client.post("/api/daysheet/delete", json={"id": "e-1"})
        self.assertEqual(res.status_code, 200)
        self.assertEqual(len(self.saved["daysheet"]), 0)

    def test_daysheet_delete_done_entry(self):
        db = make_db()
        db["daysheet"] = [{"id": "e-2", "datetime": "2026-04-26T10:00:00", "listId": "list-1", "type": "done", "text": "Write report"}]
        self._patch_all(db)
        res = self.client.post("/api/daysheet/delete", json={"id": "e-2"})
        self.assertEqual(res.status_code, 200)
        self.assertEqual(len(self.saved["daysheet"]), 0)

    def test_daysheet_delete_missing_returns_400(self):
        self._patch_all(make_db())
        res = self.client.post("/api/daysheet/delete", json={"id": "nonexistent"})
        self.assertEqual(res.status_code, 400)

    # --- POST /api/continue ---

    def test_continue_task(self):
        self._patch_all(make_db())
        res = self.client.post("/api/continue", json={"list": "Work", "task": "Write report"})
        self.assertEqual(res.status_code, 200)
        types = [e["type"] for e in self.saved["daysheet"]]
        self.assertIn("continue", types)

    def test_continue_missing_task(self):
        self._patch_all(make_db())
        res = self.client.post("/api/continue", json={"list": "Work", "task": "ghost"})
        self.assertEqual(res.status_code, 400)

    # --- index ---

    def test_index_serves_html(self):
        res = self.client.get("/")
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"taskman", res.data)


if __name__ == "__main__":
    unittest.main()
