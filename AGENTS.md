# Taskman

A minimal web-based task manager built for personal daily use. Tasks are organized into lists, and lists can be optionally grouped. Each task has a name, a parent list, and an optional due date. Each authenticated user has their own JSON data file at `~/.taskman/users/<email>/db.json`.

---

### Agent Workflow

After completing each milestone item:

- Add unit tests for any new API endpoints or service logic
- Run `python -m pytest server/ -v` and confirm all pass
- Run `python -m vulture server --min-confidence 80` and confirm it has no findings
- Check off the item in the milestones section
- Run `git add . && git commit -m "<description>"`

After changes to `server/`, advise the user to restart the web server:

```bash
flask --app server run -p 5050
```

After changes to the frontend source, advise the user to rebuild:

```bash
cd client && npm run lint
cd client && npm run build
```

Then hard-refresh with Cmd+Shift+R.

Frontend changes should leave both lint and build passing.

---

### Project Structure

```
taskman/
  server/               Flask app and all backend logic
    api.py              App factory, response helpers, and all routes
    __init__.py         Re-exports create_app from api.py
    services/           Business logic called by routes
      daysheet.py       Log and continue entry operations
      tasks.py          Task CRUD operations
      utils.py          Service decorator, errors, date helpers, find/require helpers, DB mutations
    db.py               JSON persistence (~/.taskman/users/<email>/db.json)
    config.py           Shared + per-user config loader (~/.taskman/config.json, ~/.taskman/users/<email>/config.json)
    constants.py        Shared constants and DaysheetEntryType
    tests/              Pytest test suite
      test_api.py       Flask route tests
      test_auth.py      Auth, login, OAuth, and config route tests
      test_daysheet.py  Daysheet service tests
      test_tasks.py     Task service tests
      test_utils.py     Utility function tests
      utils.py          Shared test fixtures and DB patching helpers
    pytest.ini          Pytest config (pythonpath, testpaths)
  client/               Vite + React + TypeScript frontend
    style.css           Global tokens, themes, reset, layout, shared utilities
    src/
      App.tsx           Root component and route composition
      App.module.css    Layout styles (content wrapper, main, detail panel, calendar iframe)
      main.tsx          React entry point, imports global styles
      action-button.css Shared global action-button styles (`.action-btn`)
      views/            Route-level screens: CalendarView, DaysheetView, CardsView, FocusedView, LoginView
      components/       Reusable UI
        Sidebar/        Sidebar shell, nav, list/group rows, shared sidebar types
        tasks/          TaskRow, TaskCard, TaskDetail, AddTaskForm, shared task types/styles
        Topbar.tsx      Filter pills, settings menu, and theme/sound toggle container
        SettingsMenu.tsx Collapsible settings pill (sound/theme/logout) anchored top-right
        ThemeToggle.tsx Theme switcher
        SoundToggle.tsx Sound mute toggle
        icons.tsx       Shared icon components
      hooks/            App-level React hooks (useAppData, useIsMobile, useIsNarrow)
      lib/              api.ts, types.ts, utils.ts, sound.ts
    index.html
    vite.config.ts
    tsconfig.json
    package.json
```

---

### Implementation Notes

- The Flask server exposes a REST API from `create_app()` in `server/api.py`.
- Task and daysheet routes delegate to service functions in `server/services/`; list/group and daysheet-entry edit/delete routes currently mutate the DB directly in `server/api.py`.
- Service functions use typed parameters, raise `ServiceError` for validation/domain errors, and are wrapped with `service()` from `server/services/utils.py` to return `(ok: bool, message: str)`.
- API routes use `respond()` for service results and `ok()` / `fail()` for direct route mutations.
- There is no schema migration layer. Any new task fields must be backward-compatible with existing JSON records.
- `server/db.py` creates `~/.taskman/users/<email>/db.json` from `EMPTY_DB` if missing and resets to `EMPTY_DB` if the JSON is corrupt.
- `server/config.py` stores shared server config in `~/.taskman/config.json` and per-user config in `~/.taskman/users/<email>/config.json`.
- Task completion is stored as `doneAt` UTC timestamps, and daysheet entries store UTC timestamps in `datetime`.
- Backend date logic uses the authenticated user's `calendarTimezone`; the frontend syncs the browser timezone into user config.
- In local development the Flask server exposes API routes only; Vite serves the frontend separately and proxies `/api` to Flask on port 5050. In production, Flask also serves the built `client/dist` bundle with an SPA fallback (see Milestone 7).
- Routing uses React Router (`BrowserRouter`).
- Frontend organization is route-oriented: route screens live in `client/src/views/`, reusable UI lives in `client/src/components/`, shared hooks live in `client/src/hooks/`, and generic helpers/types live in `client/src/lib/`.
- Styles use CSS Modules for feature/component-local styling. Global tokens and layout styles live in `client/style.css`, and the shared `.action-btn` utility lives in `client/src/action-button.css`.
- Repeated visual constants (animation durations, icon sizes, shadow color, hover-scale factor) are CSS custom properties in `client/style.css` rather than hardcoded per-component — e.g. `--animation-d-sm/md/lg`, `--shadow-color` (theme-aware, white shadows in dark mode), `--icon-scale-hover`.

---

### Routes

| Path | View |
|---|---|
| `/` | Redirects to `/tasks` |
| `/tasks` | Cards view (all lists / filtered to a group via `?group=<id>`) |
| `/list/:listId` | Focused view for a single list |
| `/daysheet` | Day sheet with date navigation |
| `/calendar` | Embedded Google Calendar |
| `/login` | "Sign in with Google" (public) |

---

### Database Schema

```json
{
  "groups":   [{ "id": "uuid", "name": "UNSW" }],
  "lists":    [{ "id": "uuid", "name": "COMP3131", "groupId": "uuid | null", "pinned": false }],
  "tasks":    [{ "id": "uuid", "name": "Finish Assignment 5", "listId": "uuid", "due": "2026-04-30 | null", "doneAt": "2026-04-26T04:32:05Z | null", "description": "", "flagged": false, "recurIntervalDays": "7 | null" }],
  "daysheet": [{ "id": "uuid", "datetime": "2026-04-26T04:32:05Z", "listId": "uuid", "type": "log | continue | done", "text": "Talked with Baba" }]
}
```

---

### Tech Stack

- **Backend:** Python, Flask
- **Frontend:** Vite + React + TypeScript, React Router
- **Styling:** CSS Modules + global `client/style.css` + shared `client/src/action-button.css`
- **Storage:** JSON flat files (`~/.taskman/users/<email>/db.json`, `~/.taskman/users/<email>/config.json`)
- **Tests:** `python -m pytest server/ -v`
- **Frontend lint:** `cd client && npm run lint`
- **Frontend build:** `cd client && npm run build`
- **Dead code check:** `python -m vulture server --min-confidence 80`
- **CI:** `.github/workflows/ci.yml` — installs deps, builds frontend, runs tests and Vulture

---

### Milestones

##### Milestone 1 — Server

- [x] Flask server with REST API in `server/api.py`
- [x] Service layer in `server/services/`
- [x] JSON persistence in `server/db.py`
- [x] Config loader in `server/config.py`

##### Milestone 2 — Client

- [x] Cards view: all lists/groups with pending tasks, 4-column responsive grid
- [x] Focused view: single list with pending + completed tasks
- [x] Daysheet view: day sheet with date navigation
- [x] Focused view and daysheet fill full width on mobile
- [x] Filter pills: All / Week / Day
- [x] Sidebar: Calendar + Daysheet + Tasks nav, groups, lists, alphabetical with Others last
- [x] Sidebar collapses to a full-page overlay from a burger icon on mobile
- [x] Add / duplicate / mark done / undo / delete / rename / move tasks
- [x] Create / rename / delete lists and groups
- [x] Move list to group / ungroup
- [x] Add / edit / delete daysheet log entries
- [x] Continue task (logs to daysheet)
- [x] Light/dark mode toggle (persisted to `localStorage`)
- [x] React Router — URL-based navigation, browser back/forward support
- [x] CSS Modules — styles co-located with each component

##### Milestone 3 — Google Calendar

- [x] Google Calendar iframe embedded (week view by default)
- [x] Multi-calendar support via `~/.taskman/config.json`
- [x] Per-calendar color override via embed `color` param
- [x] Calendar iframe scales to viewport width and switches to agenda view on mobile
- [x] iframe kept in DOM — switching views shows/hides it instantly

###### Calendar Config (`~/.taskman/config.json`)

```json
{
  "calendars": [
    { "id": "you@gmail.com", "color": "#B39DDB" },
    { "id": "other@group.calendar.google.com", "color": "#E67C73" }
  ],
  "calendarTimezone": "America/Sydney"
}
```

Google Calendar embed colors: `#E67C73` Flamingo · `#33B679` Sage · `#B39DDB` Wisteria · `#039BE5` Peacock · `#3F51B5` Blueberry · `#7986CB` Lavender · `#8E24AA` Grape · `#F6BF26` Banana · `#F4511E` Tangerine · `#0B8043` Basil · `#D50000` Tomato · `#616161` Graphite

##### Milestone 4 — Task Descriptions

- [x] Add `description` field to task schema (backward-compatible - fill previous ones)
- [x] API endpoint to read/write a task description
- [x] Small icon on task rows when a description exists
- [x] Task detail panel: name, list, due date at top; editable textarea below; debounced save; Escape closes
- [x] Opens as side panel when wide enough, replaces main content on mobile
- [x] Raw URLs in descriptions rendered as clickable links

##### Milestone 5 — Authentication & Google OAuth ✅

Google OAuth is the sole login method — no local password. The OAuth flow both authenticates the user and retrieves the refresh token used for calendar auto-fetch. `require_auth` gates all `/api/*` routes except `oauth/*` and `auth/status`; session-backed auth via `flask-session`.

###### Google OAuth setup note

Requires a Google Cloud project with the Calendar API enabled and an OAuth 2.0 credential. Set the authorised redirect URI to `http://127.0.0.1:5050/api/oauth/callback`. Export `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` before starting the server.

##### Milestone 6 — Ownership & Multi-user ✅

Each authenticated Google user sees only their own data: DB, config, and calendar list are all scoped by the authenticated user's email (see Database Schema note above and `server/db.py` / `server/config.py`).

##### Milestone 7 — Deploy

Target a small Ubuntu VPS on DigitalOcean as the first production deployment. Serve the built frontend and Flask API on a single HTTPS domain behind `nginx`, run Flask with `gunicorn` under `systemd`, and keep per-user data on the VPS filesystem under `~/.taskman/`. The goal is to use Taskman across devices, including opening it in Safari on iPhone and saving it to the home screen. The main goals are: no hardcoded localhost URLs, secure session cookies in production, reliable same-origin auth across devices, and a documented repeatable deploy flow.

Production deployment:

- Live URL: `https://taskman.website`
- VPS stack: DigitalOcean Ubuntu, Gunicorn, nginx, systemd, Let’s Encrypt
- Production deploy guide: `deploy/README.md`
- Production OAuth callback: `https://taskman.website/api/oauth/callback`

All items complete: environment-driven URLs, production `client/dist` serving with SPA fallback, hardened session cookies in production, fail-fast on missing env vars, same-origin `/api` in the built frontend, PWA installability (`manifest.webmanifest` + icons), gunicorn/systemd/nginx deploy assets (see `deploy/README.md`), and CI coverage for all of the above.

- [ ] Manual production smoke test on desktop and iPhone Safari: login, task CRUD, daysheet add/edit/delete, calendar load, logout, hard refresh on a nested route, and home-screen launch behavior

##### Milestone 8 — Pin Lists ✅

A list can be pinned so it always appears in the daysheet for the current day, even when it has no entries. The pin toggle lives only in the focused view, to the right of the pending task count. `POST /api/pin-list` sets the flag; `GET /api/daysheet` returns a `pinnedSections` array for pinned lists with no entries that day, which the frontend merges into the timeline grouping.

##### Milestone 9 — Flag Tasks

A task can be flagged as "planned for today" — a manual intent marker, independent of due date. Flagging is a plain boolean (`flagged`) that persists across days (no auto-clear); it is cleared automatically when the task is marked done. Flagged tasks sort to the top within their list/card in cards and focused views (existing relative order otherwise preserved), with a left border in `--accent` as the visual indicator. The toggle is right-click on the task row (no dedicated button — the row has no spare space for one); right-click's default browser context menu is suppressed. `POST /api/flag-task` sets it; `GET /api/state` normalizes missing `flagged` to `false` for legacy records.

- [X] Manual: right-click a task in cards/focused view flags it (border appears, task moves to top of its list/card); right-click again unflags it; marking a flagged task done clears the flag.

##### Milestone 10 — Batch Task Addition

Generates a numbered series of tasks in one go — the motivating case is start-of-term setup, e.g. `LEC 01`–`LEC 10` due weekly. Toggled inline from the existing single-task add row (no modal, no new route/view) since it's used rarely (a few times a term) and shouldn't add permanent weight to the everyday single-add flow.

**Name generation:** no template syntax. The typed starting name has its trailing number auto-detected via a `\d+$` match, preserving zero-padding width (`LEC 01` → prefix `"LEC "`, width `2`, start `1`); each subsequent task increments that number (`LEC 02`, `LEC 03`, …). If the name has no trailing number, fall back to appending `" 2"`, `" 3"`, etc.

**Due dates:** `due_i = start_due + i * interval_days` for `i` in `range(count)`. No catch-up/skip logic — if a computed date is invalid it's just a plain date.

**Skipping an occurrence** (e.g. week 6) is not a feature — generate the full run, delete the unwanted task manually afterward.

`add_task_series` in `server/services/tasks.py` builds the name sequence and due dates and writes all tasks in one `db.load`/`db.save`; `POST /api/add-series` exposes it. Frontend: `AddTaskForm.tsx` gains a `single`/`batch` mode toggle that reuses the name/date inputs and adds interval/count number inputs.

- [X] Manual: toggle batch mode, generate a series, confirm names/dates/count are correct; confirm the row wraps sensibly at normal width and at mobile width; confirm toggling back to single mode restores the normal add flow.

##### Milestone 11 — Recurring Tasks

A task can recur: on completion it logs to the daysheet as usual, but it never enters the done list — the completed occurrence is deleted and replaced by a fresh task row for the next occurrence (same name and list, new id, due date set to the prior occurrence's own due date plus the interval — falling back to today only if it had no due date — no catch-up/skip logic). Because each occurrence is deleted on completion, there's no "already done" state to undo (beyond deleting the daysheet entry) and no way to re-complete the same occurrence — the id is simply gone, so a repeat attempt fails with "not found" rather than needing a special same-day guard. Recurrence is created via a special mode of the existing batch-add row rather than a separate flow, since a recurring task is conceptually "batch add with unlimited entries" — generated lazily, one occurrence at a time, instead of all upfront. Adds `recurIntervalDays` to the task schema (see Database Schema above).

`add_task`/`edit_task`/`duplicate_task` gained `recurIntervalDays` handling; `done_task` and the new `skip_task` share a `_replace_with_next_occurrence` helper that deletes the completed/skipped row and spawns the next occurrence (due date rolled forward from the occurrence's own prior due date, not from today). `POST /api/skip-task` exposes skip. Frontend: `RepeatIcon` marks recurring tasks and toggles recurring mode in the batch-add row; `SkipIcon` is a third `taskLeft` button shown only on recurring, non-done rows, behind a `confirm()` dialog, using the default (non-colored) action-btn hover.

- [X] Manual: create a recurring task via batch mode's `∞`-style toggle, complete it, confirm it does NOT appear in the done list and instead a new pending task appears with due date rolled forward by the interval and a daysheet entry logged; confirm the repeat icon shows on the new occurrence; edit an existing task's interval via the edit row and confirm it takes effect on its next completion; duplicate a recurring task and confirm the copy keeps the interval; confirm two same-named tasks can each be completed independently on the same day; confirm the skip button only appears on recurring, non-done rows, confirms before acting, and advances the due date without logging a daysheet entry.

##### Milestone 12 — Description Checklists

Markdown-style checkboxes inside a task's description, with a matching progress indicator on the task row. No schema change — descriptions remain a plain text field; checkbox state is encoded in the text itself as GitHub-style `- [ ]` / `- [x]` lines.

`checkboxProgress()` / `CHECKBOX_LINE` in `client/src/lib/utils.ts` parse the description text; `TaskDetail.tsx`'s read-only view renders checkbox lines as live inputs (edit mode shows raw markdown); `TaskRow.tsx` shows a right-edge `--accent` fill bar proportional to checked/total.

- [X] Manual: add `- [ ] ...` lines to a description, confirm they render as checkboxes only outside edit mode; click to check/uncheck and confirm the state persists after a refresh; confirm the row's right-edge progress bar fills correctly and stays clipped to the row's corners at 0%, partial, and 100% completion.

##### Milestone 13 — Accent Color Picker

The accent color is user-configurable and stored per-user on the server (`accentColor` in `~/.taskman/users/<email>/config.json`), so it follows the user across devices rather than living in `localStorage` like the light/dark theme. A new settings slot sits alongside the theme toggle, laid out as a full-width row like the other settings entries (same separator/hover as sound/theme/logout) with a small circular swatch centered inside, filled with the current `--accent` value; clicking it opens a native `<input type="color">`. Right-clicking the swatch resets `accentColor` to `null` (falls back to the theme's built-in default), mirroring the right-click-to-toggle pattern from Milestone 9. `--accent-bg` is derived from the picked hex by appending the same `1a` alpha suffix the built-in themes already use, so one control drives both tokens.

`GET /api/config` returns `accentColor`; `POST /api/config/accent-color` validates and persists a `#rrggbb` hex value, or clears it back to `null` when sent `null` (`require_hex_color` in `server/services/utils.py`). Frontend: `useAppData` fetches and exposes `accentColor` alongside `calendarUrl`, and a new `AccentPicker.tsx` (reusing `ThemeToggle.module.css`'s row styling) applies `--accent` / `--accent-bg` to `document.documentElement` (or clears the inline overrides on reset) and posts changes to the server.

- [ ] Manual: open settings, click the new accent swatch, pick a color, confirm the UI's accent (focus outlines, flagged-task border, filter pill, etc.) updates immediately; refresh and confirm it persists; right-click the swatch and confirm it resets to the theme default and persists after refresh; log in from another browser/session for the same user and confirm the same accent color loads there.

##### Future

- Notes panel resizing?
- Information page (maybe button in settings - opens a panel like note panel)
- Daysheet analytics - skip days with no daysheet entry
- Turn a task description into an actionable checklist (AI)
- Screen mates - overlay at the bottom right corner - can be turned off from settings - get fed and grow/transform as we complete tasks - we need animations - avatar store in the future?
