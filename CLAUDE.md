# Taskman

A minimal terminal task manager built for personal daily use. Tasks are organized into lists, and lists can be optionally grouped. Each task has a name, a parent list, and an optional due date. The primary workflow is adding tasks to lists, viewing what's due today or this week (with overdue tasks always surfaced), and marking things done. Data is stored in a flat JSON file at `~/.taskman/db.json`.

---

### Claude Workflow

After completing each milestone item:

- Add unit tests for any new commands or logic
- Run `python -m pytest tests/ -v` and confirm all pass
- Check off the item in the milestones section
- Run `git add . && git commit -m "<description>"`

---

### Commands

##### Tasks

| Command                                                  | Description                                      |
| -------------------------------------------------------- | ------------------------------------------------ |
| `taskman add "list" ["name"] [date]`                     | Add a task to a list, or just create the list    |
| `taskman done "list" "name"`                             | Mark a task as completed                         |
| `taskman undo "list" "name"`                             | Mark a completed task as pending                 |
| `taskman update "list" "name" "new_name" [new_date]` | Rename a task and/or update its due date         |
| `taskman move ("list" "group" \| "list" "name" "new_list")`                  | Move a list to a group or a task to a list                  |
| `taskman delete ("group" \| "list" ["name"])`                         | Delete group (ungroup), list, or task    |

##### Lists & Groups

| Command                              | Description                                                |
| ------------------------------------ | ---------------------------------------------------------- |
| `taskman group "list"+ "group_name"` | Assign one or more lists to a group (creates group if new) |
| `taskman ungroup "list"+`            | Remove one or more lists from their group                  |

##### Viewing

| Command                                  | Description                                             |
| ---------------------------------------- | ------------------------------------------------------- |
| `taskman ls ["list" \| "group"]`         | All pending tasks, optionally filtered by list or group |
| `taskman ls ["list" \| "group"] --today` | Overdue + due today                                     |
| `taskman ls ["list" \| "group"] --week`  | Overdue + due within 7 days                             |
| `taskman ls ["list" \| "group"] --done`  | Completed tasks, most recent first                      |

##### Day Sheets

| Command                                     | Description                                                  |
| ------------------------------------------- | ------------------------------------------------------------ |
| `taskman log "list" "text"`                 | Freeform entry into a list's day sheet                       |
| `taskman log edit "list" "text" "new_text"` | Edits daysheet entry                                         |
| `taskman log delete "list" "text"`          | Deletes daysheet entry                                       |
| `taskman continue "list" "task"`            | Logs continued task under a list                             |
| `taskman daysheet [date]`                   | View a day's sheet (default today)                           |

##### Shell Functions

| Function                   | Expands to                |
| -------------------------- | ------------------------- |
| `tls ["list" \| "group"]`  | `taskman ls`              |
| `tlsd ["list" \| "group"]` | `taskman ls --today`      |
| `tlsw ["list" \| "group"]` | `taskman ls --week`       |
| `tds [date]`               | `taskman daysheet [date]` |

---

### Database Schema

```json
{
  "groups": [
    {
      "id": "uuid",
      "name": "UNSW"
    }
  ],
  "lists": [
    {
      "id": "uuid",
      "name": "COMP3131",
      "groupId": "uuid | null"
    }
  ],
  "tasks": [
    {
      "id": "uuid",
      "name": "Finish Assignment 5",
      "listId": "uuid",
      "due": "2026-04-30 | null",
      "done": "2026-04-26 | null"
    }
  ],
  "daysheet": [
    {
      "id": "uuid",
      "datetime": "2026-04-26T14:32:05",
      "listId": "uuid",
      "type": "log | continue | done",
      "text": "Talked with Baba"
    }
  ]
}
```

---

### Tech Stack

- Python

---

### Milestones

##### Milestone 1 — Core

- [x] Project setup
- [x] Task commands: `add`, `done`, `undo`, `edit`, `move`, `delete`
- [x] List & group commands: `group`, `ungroup`
- [x] Viewing commands: `task ls`
- [x] Shell functions: `tls`, `tlsd`, `tlsw`
- [x] Completion sound and visual feedback on `task done`

##### Milestone 2 - Day Sheets

- [x] Daysheet commands `log`, `continue`, `daysheet`
- [x] Shell function: `tds [date]`

##### Milestone 3 — Web Frontend

- [x] Flask server (`web/server.py`) with REST endpoints wrapping existing command functions
- [x] Serve static frontend from `web/static/`
- [x] View: all lists/groups with pending tasks (mirrors `taskman ls`)
- [x] View: today and week filtered views (mirrors `--today`, `--week`)
- [x] View: daysheet for today (mirrors `taskman daysheet`)
- [x] Actions: add, done, undo, delete tasks inline
- [x] Actions: log and continue from the daysheet view
- [x] Live updates without full page reload
