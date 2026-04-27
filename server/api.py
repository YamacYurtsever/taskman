from datetime import date, datetime

from flask import Flask, jsonify, request

from server import config, db
from server.constants import DATE_FORMAT, DaysheetEntryType
from server.services.daysheet import add_log, continue_task
from server.services.tasks import (
    add_task,
    delete_task,
    done_task,
    edit_task,
    move_task,
    set_task_description,
    undo_task,
)
from server.services.utils import (
    ServiceError,
    delete_list,
    find_group,
    find_list,
    require_name,
)


# ─────────────────────────── Response Helpers ───────────────────────────

def ok(message=""):
    return jsonify({"ok": True, "message": message})


def fail(message, status=400):
    return jsonify({"ok": False, "message": message}), status


def respond(result):
    ok_, message = result
    return jsonify({"ok": ok_, "message": message}), 200 if ok_ else 400


# ─────────────────────────── App Factory ───────────────────────────

def create_app():
    app = Flask(__name__)

    # ─────────────────────────── Config / State ───────────────────────────

    @app.get("/api/config")
    def get_config():
        cfg = config.load()
        calendars = cfg.get("calendars", [])
        tz = cfg.get("calendarTimezone", "UTC")

        parts = []
        for calendar in calendars:
            if isinstance(calendar, dict):
                parts.append(f"src={calendar['id']}")
                if calendar.get("color"):
                    parts.append(f"color={calendar['color'].replace('#', '%23')}")
            else:
                parts.append(f"src={calendar}")

        calendar_url = (
            f"https://calendar.google.com/calendar/embed?{'&'.join(parts)}&ctz={tz}&mode=WEEK"
            if parts else ""
        )

        return jsonify({"calendarUrl": calendar_url})

    @app.get("/api/state")
    def get_state():
        data = db.load()
        tasks = [{**t, "description": t.get("description", "")} for t in data["tasks"]]
        return jsonify({
            "groups": data["groups"],
            "lists": data["lists"],
            "tasks": tasks,
            "today": date.today().isoformat(),
        })

    # ─────────────────────────── Daysheet Reads ───────────────────────────

    @app.get("/api/daysheet")
    def get_daysheet():
        target = request.args.get("date") or date.today().isoformat()

        try:
            datetime.strptime(target, DATE_FORMAT)
        except ValueError:
            return jsonify({"error": f"invalid date '{target}'"}), 400

        data = db.load()
        lists = {lst["id"]: lst for lst in data["lists"]}
        groups = {grp["id"]: grp for grp in data["groups"]}

        entries = sorted(
            (e for e in data["daysheet"] if e["datetime"][:10] == target),
            key=lambda e: e["datetime"],
        )

        enriched = []
        for entry in entries:
            lst = lists.get(entry["listId"])
            group_id = lst["groupId"] if lst else None

            enriched.append({
                **entry,
                "listName": lst["name"] if lst else "?",
                "sectionId": f"group:{group_id}" if group_id else f"list:{entry['listId']}",
                "sectionName": groups[group_id]["name"] if group_id else (lst["name"] if lst else "?"),
                "inGroup": bool(group_id),
            })

        return jsonify({"date": target, "entries": enriched})

    # ─────────────────────────── Task Routes ───────────────────────────

    @app.post("/api/add")
    def api_add():
        body = request.get_json(force=True) or {}
        return respond(add_task(
            body.get("list", ""),
            body.get("name", ""),
            body.get("due"),
        ))

    @app.post("/api/edit")
    def api_edit():
        body = request.get_json(force=True) or {}
        return respond(edit_task(
            body.get("list", ""),
            body.get("name", ""),
            body.get("newName"),
            body.get("due"),
            "due" in body,
        ))

    @app.post("/api/delete")
    def api_delete():
        body = request.get_json(force=True) or {}
        return respond(delete_task(
            body.get("list", ""),
            body.get("name", ""),
        ))

    @app.post("/api/move-task")
    def api_move_task():
        body = request.get_json(force=True) or {}
        return respond(move_task(
            body.get("list", ""),
            body.get("name", ""),
            body.get("newList", ""),
        ))

    @app.post("/api/done")
    def api_done():
        body = request.get_json(force=True) or {}
        return respond(done_task(
            body.get("list", ""),
            body.get("name", ""),
        ))

    @app.post("/api/undo")
    def api_undo():
        body = request.get_json(force=True) or {}
        return respond(undo_task(
            body.get("list", ""),
            body.get("name", ""),
        ))

    @app.post("/api/task-description")
    def api_task_description():
        body = request.get_json(force=True) or {}
        return respond(set_task_description(
            body.get("list", ""),
            body.get("name", ""),
            body.get("description", ""),
        ))

    # ─────────────────────────── List Routes ───────────────────────────

    @app.post("/api/add-list")
    def api_add_list():
        body = request.get_json(force=True) or {}

        try:
            list_name = require_name(body.get("list"))

            data = db.load()
            if find_list(data, list_name):
                raise ServiceError(f"list '{list_name}' already exists")

            data["lists"].append({
                "id": db.new_id(),
                "name": list_name,
                "groupId": None,
            })

            db.save(data)
            return ok()
        except ServiceError as e:
            return fail(str(e))

    @app.post("/api/rename-list")
    def api_rename_list():
        body = request.get_json(force=True) or {}

        try:
            list_name = body.get("list", "")
            new_name = require_name(body.get("newName"))

            data = db.load()

            lst = find_list(data, list_name)
            if not lst:
                raise ServiceError(f"list '{list_name}' not found")

            existing = find_list(data, new_name)
            if existing and existing["id"] != lst["id"]:
                raise ServiceError(f"list '{new_name}' already exists")

            lst["name"] = new_name
            db.save(data)
            return ok()
        except ServiceError as e:
            return fail(str(e))

    @app.post("/api/delete-list")
    def api_delete_list():
        body = request.get_json(force=True) or {}

        try:
            list_name = body.get("list", "")

            data = db.load()
            lst = find_list(data, list_name)
            if not lst:
                raise ServiceError(f"list '{list_name}' not found")

            delete_list(data, lst)

            db.save(data)
            return ok()
        except ServiceError as e:
            return fail(str(e))

    @app.post("/api/move-list")
    def api_move_list():
        body = request.get_json(force=True) or {}

        try:
            list_name = body.get("list", "")
            group_name = body.get("group", None)

            data = db.load()

            lst = find_list(data, list_name)
            if not lst:
                raise ServiceError(f"list '{list_name}' not found")

            if group_name == "":
                lst["groupId"] = None
            else:
                group = find_group(data, group_name)
                if not group:
                    raise ServiceError(f"group '{group_name}' not found")
                lst["groupId"] = group["id"]

            db.save(data)
            return ok()
        except ServiceError as e:
            return fail(str(e))

    # ─────────────────────────── Group Routes ───────────────────────────

    @app.post("/api/rename-group")
    def api_rename_group():
        body = request.get_json(force=True) or {}

        try:
            group_name = body.get("group", "")
            new_name = require_name(body.get("newName"))

            data = db.load()

            group = find_group(data, group_name)
            if not group:
                raise ServiceError(f"group '{group_name}' not found")

            existing = find_group(data, new_name)
            if existing and existing["id"] != group["id"]:
                raise ServiceError(f"group '{new_name}' already exists")

            group["name"] = new_name
            db.save(data)
            return ok()
        except ServiceError as e:
            return fail(str(e))

    @app.post("/api/delete-group")
    def api_delete_group():
        body = request.get_json(force=True) or {}

        try:
            group_name = body.get("group", "")

            data = db.load()

            group = find_group(data, group_name)
            if not group:
                raise ServiceError(f"group '{group_name}' not found")

            for lst in data["lists"]:
                if lst["groupId"] == group["id"]:
                    lst["groupId"] = None

            data["groups"] = [g for g in data["groups"] if g["id"] != group["id"]]

            db.save(data)
            return ok()
        except ServiceError as e:
            return fail(str(e))

    # ─────────────────────────── Daysheet Routes ───────────────────────────

    @app.post("/api/log")
    def api_log():
        body = request.get_json(force=True) or {}
        return respond(add_log(
            body.get("list", ""),
            body.get("text", ""),
        ))

    @app.post("/api/continue")
    def api_continue():
        body = request.get_json(force=True) or {}
        return respond(continue_task(
            body.get("list", ""),
            body.get("task", ""),
        ))

    @app.post("/api/daysheet/edit")
    def api_daysheet_edit():
        body = request.get_json(force=True) or {}

        try:
            entry_id = body.get("id", "")
            new_text = require_name(body.get("text"), "text")

            data = db.load()

            entry = next((e for e in data["daysheet"] if e["id"] == entry_id), None)
            if not entry:
                raise ServiceError("entry not found")

            if entry["type"] != DaysheetEntryType.LOG:
                raise ServiceError("only log entries can be edited")

            entry["text"] = new_text

            db.save(data)
            return ok()
        except ServiceError as e:
            return fail(str(e))

    @app.post("/api/daysheet/delete")
    def api_daysheet_delete():
        body = request.get_json(force=True) or {}
        entry_id = body.get("id", "")

        data = db.load()

        before = len(data["daysheet"])
        data["daysheet"] = [e for e in data["daysheet"] if e["id"] != entry_id]

        if len(data["daysheet"]) == before:
            return fail("entry not found")

        db.save(data)
        return ok()

    return app
