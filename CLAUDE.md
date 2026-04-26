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
| `taskman edit ("list"\|"group") "new_name"`          | Rename a list or group                           |
| `taskman edit "list" "name" "new_name" [new_date]`   | Rename a task and/or update its due date         |
| `taskman move "list" "group"`                            | Assign list to a group (creates group if new)    |
| `taskman move "list" ""`                                 | Remove list from its group                       |
| `taskman move "list" "name" "new_list"`                  | Move a task to another list                      |
| `taskman delete ("group" \| "list" ["name"])`                         | Delete group (ungroup), list, or task    |

##### Viewing

| Command                                  | Description                                             |
| ---------------------------------------- | ------------------------------------------------------- |
| `taskman ls ["list" \| "group"]`         | All pending tasks, optionally filtered by list or group |
| `taskman ls ["list" \| "group"] --day`   | Overdue + due today                                     |
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

##### Calendar

| Command                 | Description                              |
| ----------------------- | ---------------------------------------- |
| `taskman cal [date]`    | List calendar events (default today)     |

##### Shell Functions

| Function                   | Expands to                |
| -------------------------- | ------------------------- |
| `tls ["list" \| "group"]`  | `taskman ls`              |
| `tlsw ["list" \| "group"]` | `taskman ls --week`       |
| `tlsd ["list" \| "group"]` | `taskman ls --day`        |
| `tds [date]`               | `taskman daysheet [date]` |
| `tcd [date]`               | `taskman cal [date]`      |

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

- **Backend:** Python, Flask
- **Frontend:** Vanilla HTML / CSS / JavaScript (no build step)
- **Storage:** JSON flat file (`~/.taskman/db.json`)

---

### Milestones

##### Milestone 1 — Core

- [x] Project setup
- [x] Task commands: `add`, `done`, `undo`, `edit`, `move`, `delete`
- [x] List & group commands: `move "list" "group"`, `move "list" ""`
- [x] Viewing commands: `task ls`
- [x] Shell functions: `tls`, `tlsd`, `tlsw`
- [x] Completion sound and visual feedback on `task done`

##### Milestone 2 - Day Sheets

- [x] Daysheet commands `log`, `continue`, `daysheet`
- [x] Shell function: `tds [date]`

##### Milestone 3 — Web Frontend

###### Infrastructure
- [x] Flask server (`web/server.py`) with REST endpoints wrapping CLI command functions
- [x] Serve static frontend from `web/client/`
- [x] Live updates without full page reload

###### Views
- [x] Cards view: all lists/groups with pending tasks, 4-column responsive grid
- [x] Focused view: single list with pending + completed tasks
- [x] Daysheet view: day sheet with date navigation
- [x] Filter pills: All / Week / Day
- [x] Sidebar: Daysheet + Tasks nav, groups, lists, alphabetical with Others last

###### Task Actions
- [x] Add task (inline per card, inline in focused view, quick-add modal Cmd+K)
- [x] Mark done / undo (checkbox)
- [x] Delete task
- [x] Continue task (logs to daysheet)
- [ ] Rename task / update due date (`taskman edit`)
- [ ] Move task to another list (`taskman move "list" "name" "new_list"`)

###### List & Group Actions
- [x] Create list (sidebar + New List)
- [ ] Rename list (CLI: `taskman edit "list" "new_name"`)
- [ ] Delete list
- [ ] Rename group (CLI: `taskman edit "group" "new_name"`)
- [ ] Delete group
- [ ] Assign list to group / ungroup (`taskman move "list" "group"` / `taskman move "list" ""`)

###### Daysheet Actions
- [x] Add log entry
- [x] Continue task (from task cards)
- [x] Delete entry
- [ ] Edit log entry (`taskman log edit`)

##### Milestone 4 — Task Descriptions

- [ ] Add `description` field to task schema (`db.json`)
- [ ] CLI: `taskman update` supports setting/clearing description
- [ ] Terminal: show description in `taskman ls` focused view
- [ ] Web: expand task row to show/edit description inline
- [ ] Web: description visible in focused list view
- [ ] Web: add description field to quick-add modal

##### Milestone 5 — Google Calendar

- [ ] OAuth2 authentication for Google Calendar API
- [ ] Web: calendar view embedded in taskman showing upcoming events
- [ ] Sidebar nav entry to access the calendar view
- [ ] Date navigation (day/week views)
- [ ] `taskman cal [date]` command to list upcoming events in the terminal
- [ ] Shell function: `tcd [date]` → `taskman cal [date]`

##### Milestone 6 — Backups

- [ ] On each `db.save()`, write/overwrite a snapshot to `~/.taskman/backups/db.YYYY-MM-DD.json` (always reflects the latest state for that day)
- [ ] Keep only the last 10 snapshots (days with writes), pruning older ones automatically
- [ ] `taskman backup` command to force a snapshot immediately (useful before bulk changes)
- [ ] `taskman restore [date]` command to restore from a snapshot (lists available dates if none given)

##### Milestone 7 — iCloud Sync

- [ ] Config file (`~/.taskman/config.json`) with configurable `db_path`
- [ ] Default `db_path` to `~/Library/Mobile Documents/com~apple~CloudDocs/taskman/db.json` when iCloud Drive is detected
- [ ] CLI flag / env var to override `db_path` at runtime
- [ ] Graceful handling of iCloud file availability (file temporarily unavailable during sync)
- [ ] Document iCloud setup in README
