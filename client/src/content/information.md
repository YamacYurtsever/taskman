# Philosophy

Taskman is a minimal, personal task manager, not a project-management tool. There's one user per install, no sharing, no assignees, no comments — just a fast way to keep track of what you're doing and when.

The design leans on three ideas: tasks live in **lists**, lists can be optionally grouped, and a lightweight **daysheet** captures what actually happened on a given day, separate from what's still pending. Nothing here tries to be smart on your behalf — due dates, recurrence, and flags are all things you set explicitly, and the app just keeps them organized.

See [Groups, Lists, and Dates](#groups-lists-and-dates) for how that structure plays out, and [Batch Add, Recurring, and Flagging](#batch-add-recurring-and-flagging) for the shortcuts built on top of it.

# The Three Views

Taskman has three main screens, reachable from the sidebar.

## Tasks

A grid of cards, one per list, showing each list's pending tasks. Groups collect related lists together; ungrouped lists fall under "Others." This is the default view — an overview of everything still open, organized the way you organize your lists.

## Daysheet

A chronological log for a single day: completed tasks, manually logged notes ("continue" entries for tasks you worked on without finishing), and free-text log entries. Date navigation moves a day at a time. Pinned lists always show up here even with nothing logged yet, so a list you check daily never silently disappears from the sheet.

## Calendar

An embedded view of your connected Google Calendar(s), colored per-calendar. It's a thin layer over Google Calendar rather than a native calendar — Taskman doesn't try to replace it, just keep it one click away from your tasks.

# Groups, Lists, and Dates

Every task belongs to exactly one **list** (e.g. a class, a project, a recurring responsibility). Lists can optionally belong to a **group** (e.g. a semester, a workplace) — this is the only nesting Taskman has. There's no sub-lists, no tags, no arbitrary hierarchy.

The other axis is time. A task can have a due date, and separately can be **flagged** — a manual "planned for today" marker independent of the due date. Between the two, most of what Taskman shows you is really a query along list/group × date:

- Tasks view: everything pending, sliced by list and group
- Daysheet: everything that happened, sliced by day
- Filter pills (All / Week / Day): the same list of tasks, sliced by due-date range

Nothing here is computed automatically from priority or effort — the due date, the flag, and the list are the only signals, kept deliberately simple.

# Batch Add, Recurring, and Flagging

A handful of shortcuts sit on top of the basic add-task flow, all from the same inline add row.

**Batch add** generates a numbered series in one go — the motivating case is start-of-term setup, e.g. typing `LEC 01` with a weekly interval and a count of 10 generates `LEC 01` through `LEC 10`, each due a week apart. No template syntax: the trailing number in whatever you typed is detected and incremented, zero-padding preserved.

**Recurring tasks** use the same batch row, toggled to an unlimited "∞" mode instead of a fixed count. A recurring task never accumulates in your done list — completing it deletes that occurrence and immediately spawns the next one, due date rolled forward by the interval from its own prior due date. Skipping an occurrence (say, a cancelled lecture) advances the date the same way, without logging anything to the daysheet.

**Flagging** marks a task "planned for today" independent of its due date — useful for pulling something forward without changing when it's actually due. Right-click a task row to toggle it; flagged tasks sort to the top of their list and get a left accent border. The flag clears automatically once the task is done.
