import sys


USAGE = """taskman — minimal terminal task manager

Usage:
  taskman add "list" "name" [date]
  taskman done "list" "name"
  taskman undo "list" "name"
  taskman update "list" "old_name" "new_name" [new_date]
  taskman move "list" "name" "new_list"
  taskman delete "list" "name"
  taskman group "list"+ "group_name"
  taskman ungroup "list"+
  taskman ls ["list" | "group"] [--today | --week]
  taskman log "list" "text"
  taskman log edit "list" "text" "new_text"
  taskman log del "list" "text"
  taskman continue "list" "task"
  taskman daysheet [date]
"""


def main():
    args = sys.argv[1:]

    if not args or args[0] in ("-h", "--help"):
        print(USAGE)
        return

    cmd = args[0]

    if cmd == "add":
        from taskman.commands.tasks import cmd_add
        cmd_add(args[1:])
    elif cmd == "done":
        from taskman.commands.tasks import cmd_done
        cmd_done(args[1:])
    elif cmd == "undo":
        from taskman.commands.tasks import cmd_undo
        cmd_undo(args[1:])
    elif cmd == "update":
        from taskman.commands.tasks import cmd_update
        cmd_update(args[1:])
    elif cmd == "move":
        from taskman.commands.tasks import cmd_move
        cmd_move(args[1:])
    elif cmd == "delete":
        from taskman.commands.tasks import cmd_delete
        cmd_delete(args[1:])
    elif cmd == "group":
        from taskman.commands.lists import cmd_group
        cmd_group(args[1:])
    elif cmd == "ungroup":
        from taskman.commands.lists import cmd_ungroup
        cmd_ungroup(args[1:])
    elif cmd == "ls":
        from taskman.commands.view import cmd_ls
        cmd_ls(args[1:])
    elif cmd == "log":
        from taskman.commands.daysheet import cmd_log
        cmd_log(args[1:])
    elif cmd == "continue":
        from taskman.commands.daysheet import cmd_continue
        cmd_continue(args[1:])
    elif cmd == "daysheet":
        from taskman.commands.daysheet import cmd_daysheet
        cmd_daysheet(args[1:])
    else:
        print(f"taskman: unknown command '{cmd}'", file=sys.stderr)
        print(USAGE)
        sys.exit(1)
