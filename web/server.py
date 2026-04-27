import io
import re
from contextlib import redirect_stderr, redirect_stdout
from datetime import date, datetime
from pathlib import Path

from flask import Flask, jsonify, request, send_from_directory

from taskman import config, db
from taskman.commands.daysheet import cmd_continue, cmd_log
from taskman.commands.tasks import cmd_add, cmd_delete, cmd_done, cmd_undo

STATIC_DIR = Path(__file__).parent / "client"
_ANSI_RE = re.compile(r"\033\[[0-9;]*m")


def _run(fn, args):
    """Invoke a CLI command function, capturing output and SystemExit."""
    out, err = io.StringIO(), io.StringIO()
    try:
        with redirect_stdout(out), redirect_stderr(err):
            fn(args)
    except SystemExit:
        msg = _ANSI_RE.sub("", err.getvalue()).strip() or "command failed"
        msg = msg.removeprefix("taskman:").strip()
        return False, msg
    return True, _ANSI_RE.sub("", out.getvalue()).strip()


def create_app():
    app = Flask(__name__, static_folder=None)

    @app.get("/")
    def index():
        return send_from_directory(STATIC_DIR, "index.html")

    @app.get("/client/<path:name>")
    def static_files(name):
        return send_from_directory(STATIC_DIR, name)

    @app.get("/api/config")
    def get_config():
        cfg = config.load()
        calendars = cfg.get("calendars", [])
        tz = cfg.get("calendarTimezone", "UTC")
        if calendars:
            parts = []
            for c in calendars:
                if isinstance(c, dict):
                    parts.append(f"src={c['id']}")
                    if c.get("color"):
                        parts.append(f"color={c['color'].replace('#', '%23')}")
                else:
                    parts.append(f"src={c}")
            cal_url = f"https://calendar.google.com/calendar/embed?{'&'.join(parts)}&ctz={tz}&mode=WEEK"
        else:
            cal_url = ""
        return jsonify({"calendarUrl": cal_url})

    @app.get("/api/state")
    def get_state():
        data = db.load()
        return jsonify({
            "groups": data["groups"],
            "lists": data["lists"],
            "tasks": data["tasks"],
            "today": date.today().isoformat(),
        })

    @app.get("/api/daysheet")
    def get_daysheet():
        target = request.args.get("date") or date.today().isoformat()
        try:
            datetime.strptime(target, "%Y-%m-%d")
        except ValueError:
            return jsonify({"error": f"invalid date '{target}'"}), 400

        data = db.load()
        list_by_id = {l["id"]: l for l in data["lists"]}
        group_by_id = {g["id"]: g for g in data["groups"]}
        entries = sorted(
            (e for e in data["daysheet"] if e["datetime"][:10] == target),
            key=lambda e: e["datetime"],
        )
        enriched = []
        for e in entries:
            lst = list_by_id.get(e["listId"])
            gid = lst["groupId"] if lst else None
            enriched.append({
                **e,
                "listName": lst["name"] if lst else "?",
                "sectionId": f"group:{gid}" if gid else f"list:{e['listId']}",
                "sectionName": group_by_id[gid]["name"] if gid else (lst["name"] if lst else "?"),
                "inGroup": bool(gid),
            })
        return jsonify({"date": target, "entries": enriched})

    def _action(fn, args):
        ok, msg = _run(fn, args)
        status = 200 if ok else 400
        return jsonify({"ok": ok, "message": msg}), status

    @app.post("/api/add")
    def api_add():
        body = request.get_json(force=True) or {}
        args = [body.get("list", ""), body.get("name", "")]
        if body.get("due"):
            args.append(body["due"])
        return _action(cmd_add, args)

    @app.post("/api/add-list")
    def api_add_list():
        body = request.get_json(force=True) or {}
        return _action(cmd_add, [body.get("list", "")])

    @app.post("/api/done")
    def api_done():
        body = request.get_json(force=True) or {}
        return _action(cmd_done, [body.get("list", ""), body.get("name", "")])

    @app.post("/api/undo")
    def api_undo():
        body = request.get_json(force=True) or {}
        return _action(cmd_undo, [body.get("list", ""), body.get("name", "")])

    @app.post("/api/delete")
    def api_delete():
        body = request.get_json(force=True) or {}
        args = [body.get("list", "")]
        if body.get("name"):
            args.append(body["name"])
        return _action(cmd_delete, args)

    @app.post("/api/log")
    def api_log():
        body = request.get_json(force=True) or {}
        return _action(cmd_log, [body.get("list", ""), body.get("text", "")])

    @app.post("/api/daysheet/edit")
    def api_daysheet_edit():
        body = request.get_json(force=True) or {}
        entry_id = body.get("id", "")
        new_text = (body.get("text") or "").strip()
        if not new_text:
            return jsonify({"ok": False, "message": "text is required"}), 400
        data = db.load()
        entry = next((e for e in data["daysheet"] if e["id"] == entry_id), None)
        if not entry:
            return jsonify({"ok": False, "message": "entry not found"}), 400
        if entry["type"] != "log":
            return jsonify({"ok": False, "message": "only log entries can be edited"}), 400
        entry["text"] = new_text
        db.save(data)
        return jsonify({"ok": True, "message": ""})

    @app.post("/api/daysheet/delete")
    def api_daysheet_delete():
        body = request.get_json(force=True) or {}
        entry_id = body.get("id", "")
        data = db.load()
        before = len(data["daysheet"])
        data["daysheet"] = [e for e in data["daysheet"] if e["id"] != entry_id]
        if len(data["daysheet"]) == before:
            return jsonify({"ok": False, "message": "entry not found"}), 400
        db.save(data)
        return jsonify({"ok": True, "message": ""})

    @app.post("/api/edit")
    def api_edit():
        body = request.get_json(force=True) or {}
        list_name = body.get("list", "")
        name = body.get("name", "")
        new_name = body.get("newName") or name

        data = db.load()
        lst = next((l for l in data["lists"] if l["name"] == list_name), None)
        if not lst:
            return jsonify({"ok": False, "message": f"list '{list_name}' not found"}), 400
        task = next((t for t in data["tasks"] if t["listId"] == lst["id"] and t["name"] == name), None)
        if not task:
            return jsonify({"ok": False, "message": f"task '{name}' not found in '{list_name}'"}), 400
        if new_name != name and any(t["name"] == new_name and t["listId"] == lst["id"] for t in data["tasks"]):
            return jsonify({"ok": False, "message": f"task '{new_name}' already exists in '{list_name}'"}), 400
        task["name"] = new_name
        if "due" in body:
            task["due"] = body["due"] or None
        db.save(data)
        return jsonify({"ok": True, "message": ""})

    @app.post("/api/continue")
    def api_continue():
        body = request.get_json(force=True) or {}
        return _action(cmd_continue, [body.get("list", ""), body.get("task", "")])

    return app


def main():
    import argparse
    parser = argparse.ArgumentParser(description="taskman web frontend")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=5050)
    parser.add_argument("--debug", action="store_true")
    args = parser.parse_args()
    create_app().run(host=args.host, port=args.port, debug=args.debug)


if __name__ == "__main__":
    main()
