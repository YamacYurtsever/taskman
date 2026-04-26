import subprocess
import sys
from datetime import date, datetime
from taskman import db

_SOUND = "/System/Library/Sounds/Glass.aiff"


def _play_sound():
    try:
        subprocess.Popen(["afplay", _SOUND], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except FileNotFoundError:
        pass


def _err(msg):
    print(f"taskman: {msg}", file=sys.stderr)
    sys.exit(1)


def _parse_date(s):
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y"):
        try:
            return datetime.strptime(s, fmt).strftime("%Y-%m-%d")
        except ValueError:
            pass
    _err(f"invalid date '{s}' — expected YYYY-MM-DD")


def _find_list(data, name):
    return next((l for l in data["lists"] if l["name"] == name), None)


def _get_or_create_list(data, name):
    lst = _find_list(data, name)
    if not lst:
        lst = {"id": db.new_id(), "name": name, "groupId": None}
        data["lists"].append(lst)
    return lst


def _find_task(data, list_id, name):
    return next(
        (t for t in data["tasks"] if t["listId"] == list_id and t["name"] == name),
        None,
    )


def cmd_add(args):
    if len(args) < 1:
        _err('usage: taskman add "list" ["name"] [date]')
    list_name = args[0]

    data = db.load()
    lst = _get_or_create_list(data, list_name)

    if len(args) == 1:
        db.save(data)
        print(f"+ [{list_name}]")
        return

    task_name = args[1]
    due = _parse_date(args[2]) if len(args) >= 3 else None

    if _find_task(data, lst["id"], task_name):
        _err(f"task '{task_name}' already exists in '{list_name}'")

    data["tasks"].append({
        "id": db.new_id(),
        "name": task_name,
        "listId": lst["id"],
        "due": due,
        "done": None,
    })
    db.save(data)
    suffix = f" · due {due}" if due else ""
    print(f"+ [{list_name}] {task_name}{suffix}")


def cmd_done(args):
    if len(args) < 2:
        _err('usage: taskman done "list" "name"')
    list_name, task_name = args[0], args[1]

    data = db.load()
    lst = _find_list(data, list_name)
    if not lst:
        _err(f"list '{list_name}' not found")

    task = _find_task(data, lst["id"], task_name)
    if not task:
        _err(f"task '{task_name}' not found in '{list_name}'")
    if task["done"]:
        _err(f"task '{task_name}' is already done")

    today = date.today().isoformat()
    data["daysheet"] = [
        e for e in data["daysheet"]
        if not (e["listId"] == lst["id"] and e["type"] == "continue"
                and e["text"] == task_name and e["datetime"][:10] == today)
    ]
    data["daysheet"].append({
        "id": db.new_id(),
        "datetime": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
        "listId": lst["id"],
        "type": "done",
        "text": task_name,
    })
    task["done"] = today
    db.save(data)
    print(f"\033[32m✓ [{list_name}] {task_name}\033[0m")
    _play_sound()


def cmd_undo(args):
    if len(args) < 2:
        _err('usage: taskman undo "list" "name"')
    list_name, task_name = args[0], args[1]

    data = db.load()
    lst = _find_list(data, list_name)
    if not lst:
        _err(f"list '{list_name}' not found")

    task = _find_task(data, lst["id"], task_name)
    if not task:
        _err(f"task '{task_name}' not found in '{list_name}'")
    if not task["done"]:
        _err(f"task '{task_name}' is not done")

    task["done"] = None
    db.save(data)
    print(f"○ [{list_name}] {task_name}")


def cmd_update(args):
    if len(args) < 3:
        _err('usage: taskman update "list" "old_name" "new_name" [new_date]')
    list_name, old_name, new_name = args[0], args[1], args[2]
    new_due = _parse_date(args[3]) if len(args) >= 4 else ...  # ... = not provided

    data = db.load()
    lst = _find_list(data, list_name)
    if not lst:
        _err(f"list '{list_name}' not found")

    task = _find_task(data, lst["id"], old_name)
    if not task:
        _err(f"task '{old_name}' not found in '{list_name}'")

    if new_name != old_name and _find_task(data, lst["id"], new_name):
        _err(f"task '{new_name}' already exists in '{list_name}'")

    task["name"] = new_name
    if new_due is not ...:
        task["due"] = new_due
    db.save(data)
    due_str = f" · due {task['due']}" if task["due"] else ""
    print(f"~ [{list_name}] {new_name}{due_str}")


def _get_or_create_group(data, name):
    group = _find_group(data, name)
    if not group:
        group = {"id": db.new_id(), "name": name}
        data["groups"].append(group)
    return group


def cmd_move(args):
    if len(args) < 2:
        _err('usage: taskman move "list" "group" | taskman move "list" "name" "new_list"')
    list_name = args[0]

    data = db.load()

    if len(args) == 2:
        group_name = args[1]
        lst = _find_list(data, list_name)
        if not lst:
            _err(f"list '{list_name}' not found")
        group = _get_or_create_group(data, group_name)
        lst["groupId"] = group["id"]
        db.save(data)
        print(f"→ [{list_name}] → group '{group_name}'")
    else:
        task_name, new_list_name = args[1], args[2]
        lst = _find_list(data, list_name)
        if not lst:
            _err(f"list '{list_name}' not found")
        task = _find_task(data, lst["id"], task_name)
        if not task:
            _err(f"task '{task_name}' not found in '{list_name}'")
        new_lst = _get_or_create_list(data, new_list_name)
        if _find_task(data, new_lst["id"], task_name):
            _err(f"task '{task_name}' already exists in '{new_list_name}'")
        task["listId"] = new_lst["id"]
        db.save(data)
        print(f"→ {task_name}  [{list_name}] → [{new_list_name}]")


def _find_group(data, name):
    return next((g for g in data["groups"] if g["name"] == name), None)


def cmd_delete(args):
    if len(args) < 1:
        _err('usage: taskman delete "list" ["name"]')
    name = args[0]

    data = db.load()

    if len(args) == 1:
        group = _find_group(data, name)
        if group:
            for l in data["lists"]:
                if l["groupId"] == group["id"]:
                    l["groupId"] = None
            data["groups"] = [g for g in data["groups"] if g["id"] != group["id"]]
            db.save(data)
            print(f"- group '{name}'")
            return

        lst = _find_list(data, name)
        if not lst:
            _err(f"'{name}' not found")
        group_id = lst["groupId"]
        data["tasks"] = [t for t in data["tasks"] if t["listId"] != lst["id"]]
        data["daysheet"] = [e for e in data["daysheet"] if e["listId"] != lst["id"]]
        data["lists"] = [l for l in data["lists"] if l["id"] != lst["id"]]
        if group_id and not any(l["groupId"] == group_id for l in data["lists"]):
            data["groups"] = [g for g in data["groups"] if g["id"] != group_id]
        db.save(data)
        print(f"- [{name}]")
    else:
        lst = _find_list(data, name)
        if not lst:
            _err(f"list '{name}' not found")
        task_name = args[1]
        task = _find_task(data, lst["id"], task_name)
        if not task:
            _err(f"task '{task_name}' not found in '{name}'")
        data["tasks"] = [t for t in data["tasks"] if t["id"] != task["id"]]
        db.save(data)
        print(f"- [{name}] {task_name}")
