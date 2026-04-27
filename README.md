# Taskman

A minimal terminal task manager for personal daily use. Tasks live in lists, lists can be grouped, and everything is stored in a flat JSON file at `~/.taskman/db.json`.

---

## Install

```bash
pip install -e .
```

---

## Usage

### Tasks

```bash
taskman add "list" ["name"] [date]              # Add a task (date: YYYY-MM-DD), or just create the list
taskman done "list" "name"                      # Mark done
taskman undo "list" "name"                      # Mark pending
taskman edit ("list"|"group") "new_name"        # Rename a list or group
taskman edit "list" "name" "new_name" [date]    # Rename a task and/or update its due date
taskman move "list" "group"                     # Assign list to a group (creates group if new)
taskman move "list" ""                          # Remove list from its group
taskman move "list" "name" "new_list"           # Move task to another list
taskman delete ("group"|"list" ["name"])        # Delete a group, list, or task
```

### Viewing

```bash
taskman ls [list|group]                         # All pending tasks
taskman ls [list|group] --day                   # Overdue + due today
taskman ls [list|group] --week                  # Overdue + due this week
taskman ls [list|group] --done                  # Completed tasks, most recent first
```

### Day Sheets

```bash
taskman log "list" "text"                       # Add a freeform log entry
taskman log edit "list" "text" "new_text"       # Edit a log entry
taskman log delete "list" "text"                # Delete a log entry
taskman continue "list" "task"                  # Log a continued task (once per day)
taskman daysheet [date]                         # View day sheet (default: today)
```

### Shell Aliases

```bash
tls [list|group]                                # taskman ls
tlsd [list|group]                               # taskman ls --day
tlsw [list|group]                               # taskman ls --week
tds [date]                                      # taskman daysheet
```

---

## Web UI

```bash
taskman web
```

Opens a local web interface at `http://127.0.0.1:5050` with:

- Cards view of all lists and groups with pending tasks
- Focused view per list with pending + completed tasks
- Daysheet view with date navigation and log entry form
- Google Calendar embed (week view, multi-calendar support)
- Filter pills: All / Week / Day
- Inline task add, mark done, delete, rename, move, and continue
- Light/dark mode

```bash
taskman web --port 8080 --debug
```

### Calendar Config

Create `~/.taskman/config.json` to configure which calendars appear:

```json
{
  "calendars": [
    { "id": "you@gmail.com", "color": "#B39DDB" },
    { "id": "other@group.calendar.google.com", "color": "#E67C73" }
  ],
  "calendarTimezone": "America/Sydney"
}
```
