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
taskman add "list" "name" [date]          # Add a task (date: YYYY-MM-DD)
taskman done "list" "name"                # Mark done
taskman undo "list" "name"                # Mark pending
taskman update "list" "name" "new_name" [new_date]
taskman move "list" "name" "new_list"     # Move task to another list
taskman delete "list" "name"              # Delete a task
```

### Lists & Groups

```bash
taskman group "list"+ "group_name"        # Add lists to a group
taskman ungroup "list"+                   # Remove lists from their group
taskman move "list" "group"               # Move list to a group
taskman delete "group"                    # Delete group (ungroup lists)
taskman delete "list"                     # Delete a list
```

### Viewing

```bash
taskman ls [list|group]                   # All pending tasks
taskman ls [list|group] --day             # Overdue + due today
taskman ls [list|group] --week            # Overdue + due this week
taskman ls [list|group] --done            # Completed tasks
```

### Day Sheets

```bash
taskman log "list" "text"                 # Add a freeform log entry
taskman log edit "list" "text" "new"      # Edit a log entry
taskman log del "list" "text"             # Delete a log entry
taskman continue "list" "task"            # Log a continued task
taskman daysheet [date]                   # View day sheet (default: today)
```

### Shell Aliases

```bash
tls [list|group]                          # taskman ls
tlsd [list|group]                         # taskman ls --day
tlsw [list|group]                         # taskman ls --week
tds [date]                                # taskman daysheet
```

---

## Web UI

```bash
taskman web
```

Opens a local web interface mirroring the CLI views with inline task actions.
