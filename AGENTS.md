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
        Topbar.tsx      Filter pills and theme toggle container
        ThemeToggle.tsx Theme switcher
        icons.tsx       Shared icon components
      hooks/            App-level React hooks (for example `useAppData`)
      lib/              api.ts, types.ts, utils.ts
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
- The Flask server currently exposes API routes only; it does not serve the frontend bundle.
- The frontend is built with Vite. In dev mode, Vite proxies `/api` to the Flask server on port 5050.
- Routing uses React Router (`BrowserRouter`).
- Frontend organization is route-oriented: route screens live in `client/src/views/`, reusable UI lives in `client/src/components/`, shared hooks live in `client/src/hooks/`, and generic helpers/types live in `client/src/lib/`.
- Styles use CSS Modules for feature/component-local styling. Global tokens and layout styles live in `client/style.css`, and the shared `.action-btn` utility lives in `client/src/action-button.css`.

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

##### Milestone 5 — Authentication & Google OAuth

Google OAuth is the sole login method — no local password. The OAuth flow both authenticates the user and retrieves the refresh token used for calendar auto-fetch.

###### Setup & config

- [x] `requirements.txt` — `flask-session`, `google-auth-oauthlib`, `google-api-python-client`
- [x] `server/constants.py` — add `SESSIONS_PATH = TASKMAN_DIR / "sessions"`
- [x] `server/config.py` — add `save()`; extend `DEFAULTS` with `secretKey`, `googleRefreshToken`, `googleEmail`
- [x] `.github/workflows/ci.yml` — install from `requirements.txt` instead of inline pip list
- [x] `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET` read from environment; never committed

###### Backend

- [x] `server/api.py` — `flask-session` setup; auto-generate `secretKey` and persist to `config.json` on first run
- [x] `server/api.py` — `require_auth` decorator (checks `session["authenticated"]`); applied to all `/api/*` except oauth/callback and auth/status
- [x] `server/api.py` — `GET /api/auth/status` → `{authenticated}` (public)
- [x] `server/api.py` — `GET /api/oauth/start` → return Google consent URL; `GET /api/oauth/callback` → store refresh token + email, set session, redirect to `/`; `POST /api/logout`; set `OAUTHLIB_INSECURE_TRANSPORT=1` in dev; use `access_type="offline"&prompt="consent"`
- [x] `server/api.py` — `GET /api/config` updated to fetch calendar list from Google Calendar API using stored refresh token

###### Backend — tests

- [x] `server/tests/utils.py` — add `saved_config` context manager (mirrors `saved_db`)
- [x] `server/tests/test_api.py` — seed `session["authenticated"] = True` in `setUp` so existing tests pass through `require_auth`
- [x] `server/tests/test_auth.py` — auth status, OAuth start/callback/logout, config calendar fetch

###### Frontend

- [x] `client/src/lib/types.ts` — `AuthStatusResponse`
- [x] `client/src/lib/api.ts` — auth/OAuth entries in `API`; `setUnauthorizedHandler` for global 401 redirect
- [x] `client/src/views/LoginView.tsx` + `LoginView.module.css` — "Sign in with Google" button only; calls `/api/oauth/start` and redirects to the returned URL
- [x] `client/src/App.tsx` — rename `App` → `AuthenticatedApp`; new `App` checks auth status and renders `LoginView` or `AuthenticatedApp`; add a single logout button in the authenticated layout
- [x] `client/src/hooks/useAppData.ts` — expose `logout` function

###### Google OAuth setup note

Requires a Google Cloud project with the Calendar API enabled and an OAuth 2.0 credential. Set the authorised redirect URI to `http://127.0.0.1:5050/api/oauth/callback`. Export `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` before starting the server.

##### Milestone 6 — Ownership & Multi-user

Each authenticated Google user sees only their own data.

###### Backend

- [x] `server/db.py` — scope `DB_PATH` per user (e.g. `~/.taskman/users/<email>/db.json`); derive path from the authenticated user's email passed into `db.load()` / `db.save()`
- [x] `server/config.py` — keep a single shared `config.json` for server-level settings (`secretKey`, OAuth credentials); move per-user state (`googleRefreshToken`, `googleEmail`, calendars) into the per-user DB or a per-user config file
- [x] `server/api.py` — pass authenticated user's email into all `db.load()` / `db.save()` calls; store `email` in session on OAuth callback
- [x] `server/api.py` — `GET /api/config` fetches calendar list using the requesting user's own refresh token
- [x] `server/api.py` / `server/services/*` — use the authenticated user's `calendarTimezone` for server-side "today" and timestamp handling

###### Backend — tests

- [x] Update `saved_db` / `saved_config` fixtures and all route tests to account for per-user DB paths
- [x] Add multi-user isolation tests (two users cannot read each other's data)

###### Frontend

- [x] No frontend changes required — API contract is unchanged

##### Milestone 7 — Deploy

Target a small Ubuntu VPS on DigitalOcean as the first production deployment. Serve the built frontend and Flask API on a single HTTPS domain behind `nginx`, run Flask with `gunicorn` under `systemd`, and keep per-user data on the VPS filesystem under `~/.taskman/`. The goal is to use Taskman across devices, including opening it in Safari on iPhone and saving it to the home screen. The main goals are: no hardcoded localhost URLs, secure session cookies in production, reliable same-origin auth across devices, and a documented repeatable deploy flow.

Production deployment:

- Live URL: `https://taskman.website`
- VPS stack: DigitalOcean Ubuntu, Gunicorn, nginx, systemd, Let’s Encrypt
- Production deploy guide: `deploy/README.md`
- Production OAuth callback: `https://taskman.website/api/oauth/callback`

###### Backend

- [x] `server/constants.py` / `server/services/auth.py` — replace hardcoded `FRONTEND_URL` and OAuth `REDIRECT_URI` with environment-driven production URLs (for example `TASKMAN_BASE_URL`) while keeping local development defaults
- [x] `server/api.py` — serve the built `client/dist` bundle in production with an SPA fallback route, while preserving Vite dev mode for local development
- [x] `server/api.py` — tighten production session config (`SESSION_COOKIE_SECURE`, `SESSION_COOKIE_SAMESITE`, `SESSION_COOKIE_HTTPONLY`) and only enable `OAUTHLIB_INSECURE_TRANSPORT=1` in local development
- [x] `server/config.py` / startup path — fail clearly when required production env vars are missing instead of surfacing vague OAuth/runtime failures

###### Backend — tests

- [x] Add tests for environment-driven frontend/callback URL generation
- [x] Add tests for production frontend serving / SPA fallback behavior
- [x] Add tests for production session config branches

###### Frontend

- [x] `client/src/lib/api.ts` / Vite config — keep `/api` same-origin in production and retain the existing dev proxy behavior locally
- [x] `client` build output — verify direct navigation to `/tasks`, `/daysheet`, `/calendar`, and `/list/:listId` works through the production SPA fallback
- [x] Add minimal installability support for Safari / home-screen usage: `manifest.webmanifest`, app icons, and iOS-friendly metadata in the built frontend shell

###### Ops / deploy assets

- [x] Add a production WSGI entrypoint and document the DigitalOcean Ubuntu `gunicorn` command used to run the Flask app
- [x] Add deploy assets under a repo-owned location (for example `deploy/`) for a `systemd` service and an `nginx` site config that proxies to Gunicorn and serves HTTPS on the VPS
- [x] Document required production environment variables (`GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `TASKMAN_BASE_URL`, and any Flask environment settings) and where they are loaded from
- [x] Document Google OAuth production setup for the public DigitalOcean-hosted domain: authorised origin(s), authorised redirect URI, and the need to update them when the public domain changes
- [x] Document Let’s Encrypt setup and HTTPS renewal on the VPS
- [x] Document persistence and backup expectations for `~/.taskman/` on the VPS so deploys do not overwrite user DB/config/session data
- [x] Keep deployment removable by documenting a future `TASKMAN_DIR` override or export/import path so the same data can be moved back to a local machine without rewriting the schema

###### CI

- [x] Update `.github/workflows/ci.yml` to keep deployment-critical checks in CI, including backend tests, Vulture, frontend lint/build, and any new production-serving tests added for Milestone 7

###### Deploy verification

- [x] `python -m pytest server/ -v`
- [x] `python -m vulture server --min-confidence 80`
- [x] `cd client && npm run lint`
- [x] `cd client && npm run build`
- [ ] Manual production smoke test on desktop and iPhone Safari: login, task CRUD, daysheet add/edit/delete, calendar load, logout, hard refresh on a nested route, and home-screen launch behavior

##### Milestone 8 — Pin Lists

A list can be pinned so it always appears in the daysheet for the current day, even when it has no entries. The pin toggle lives only in the focused view, to the right of the pending task count.

###### Schema

- [x] `server/constants.py` — add `pinned: false` to the list object in `EMPTY_DB` (backward-compatible; existing lists without the field are treated as unpinned).

Updated list schema:

```json
{ "id": "uuid", "name": "COMP3131", "groupId": "uuid | null", "pinned": false }
```

###### Backend

- [x] `server/api.py` — `POST /api/pin-list` — accepts `{ listId, pinned: bool }` body; finds the list by ID and sets its `pinned` field; returns `ok()` / `fail()`; requires auth. Follow the same pattern as `rename-list` and `delete-list`.
- [x] `server/api.py` — `GET /api/state` — `pinned` field is already present on list objects in the DB; no extra mapping needed as long as the raw list objects are returned (verify this is the case).
- [x] `server/api.py` — `GET /api/daysheet` — extend the response with a `pinnedSections` key: an array of `{ sectionId, sectionName, inGroup }` objects for every pinned list that has **no entries** on the requested date. A pinned list that already has entries appears only in `entries` (not duplicated in `pinnedSections`). Section shape mirrors the enriched entry fields so the frontend can reuse the same grouping logic.

###### Backend — tests

- [x] `server/tests/test_api.py` — test `POST /api/pin-list`: pin a list, verify `pinned` is `true` in DB; unpin, verify `false`; 404 for unknown list ID.
- [x] `server/tests/test_api.py` — test `GET /api/daysheet` with a pinned list that has no entries: `pinnedSections` contains the list's section. Test that a pinned list with at least one entry on the day does **not** appear in `pinnedSections`. Test that an unpinned list with no entries does not appear in `pinnedSections`.

###### Frontend

- [x] `client/src/lib/types.ts` — add `pinned?: boolean` to `TaskList`; add `pinnedSections: Array<{ sectionId: string; sectionName: string; inGroup: boolean }>` to `DaysheetResponse`.
- [x] `client/src/lib/api.ts` — add `pinList: '/api/pin-list'` to the `API` const object.
- [x] `client/src/components/icons.tsx` — add `PinIcon` (outline/filled SVG; filled when pinned). Use a simple thumbtack or pin SVG matching the existing icon style.
- [x] `client/src/views/FocusedView.tsx` — add a `PinIcon` button immediately to the right of the `<span className={styles.focusedMeta}>{pending.length}</span>` badge. Clicking it calls `act(API.pinList, { listId: list.id, pinned: !list.pinned })`. The icon renders filled when `list.pinned` is `true`. The button should use the existing `action-btn` class pattern for consistent hover styling.
- [x] `client/src/views/DaysheetView.tsx` — pass `pinnedSections` from `DaysheetResponse` into `Timeline`. In `groupEntries`, after building sections from entries, append any `pinnedSections` entries whose `sectionId` is not already in the map (renders the section header with no entry rows, so the section appears empty but visible).
- [x] Styles — add pin button positioning styles in `Tasks.module.css` alongside the existing `focusedMeta` styles (small, vertically centred, no extra margin needed beyond the existing gap).

##### Milestone 9 — Flag Tasks

A task can be flagged as "planned for today" — a manual intent marker, independent of due date. Flagging is a plain boolean (`flagged`) that persists across days (no auto-clear); it is cleared automatically when the task is marked done. Flagged tasks sort to the top within their list/card in cards and focused views (existing relative order otherwise preserved), with a left border in `--accent-hl` as the visual indicator. The toggle is right-click on the task row (no dedicated button — the row has no spare space for one); right-click's default browser context menu is suppressed.

Updated task schema:

```json
{ "id": "uuid", "name": "Finish Assignment 5", "listId": "uuid", "due": "2026-04-30 | null", "doneAt": "2026-04-26T04:32:05Z | null", "description": "", "flagged": false }
```

###### Backend

- [x] `server/services/tasks.py` — `flag_task(task_id, flagged, email=None, tz_name="UTC")`; sets the `flagged` field on the task found via `require_task_by_id`. Same shape as other id-based task services.
- [x] `server/services/tasks.py` — `add_task` sets `"flagged": False` on new tasks; `duplicate_task` sets `"flagged": False` on the duplicate (the flag does not carry over to copies).
- [x] `server/services/tasks.py` — `done_task` clears `flagged` to `False` when a task is marked done.
- [x] `server/api.py` — `POST /api/flag-task` — accepts `{ taskId, flagged: bool }`; delegates to `flag_task`; requires auth. Follow the same pattern as `/api/pin-list`.
- [x] `server/api.py` — `GET /api/state` — normalize `flagged` with `t.get("flagged", False)` alongside the existing `description`/`doneAt` normalization, for backward compatibility with existing records that predate this field.

###### Backend — tests

- [x] `server/tests/test_tasks.py` — test `flag_task` sets/unsets `flagged`; rejects unknown task id.
- [x] `server/tests/test_tasks.py` — test `done_task` clears `flagged` on a previously-flagged task.
- [x] `server/tests/test_api.py` — test `POST /api/flag-task`; test `GET /api/state` normalizes missing `flagged` to `false` for legacy records.

###### Frontend

- [x] `client/src/lib/types.ts` — add `flagged: boolean` to `Task` (backend always normalizes it, so it's non-optional, unlike list `pinned`).
- [x] `client/src/lib/api.ts` — add `flagTask: '/api/flag-task'` to the `API` const object.
- [x] `client/src/components/tasks/TaskRow.tsx` — `onContextMenu` handler: `e.preventDefault()`, then `act(API.flagTask, { taskId: task.id, flagged: !task.flagged })`.
- [x] `client/src/components/tasks/Tasks.module.css` — flagged task rows get a left border in `var(--accent-hl)`.
- [x] `client/src/lib/utils.ts` — `pendingFor()` partitions into flagged/unflagged, sorts each partition with the existing due/name logic, and concatenates flagged first.

###### Frontend — verification

- [x] `cd client && npm run lint`
- [x] `cd client && npm run build`
- [ ] Manual: right-click a task in cards/focused view flags it (border appears, task moves to top of its list/card); right-click again unflags it; marking a flagged task done clears the flag.

##### Milestone 10 — Batch Task Addition

Generates a numbered series of tasks in one go — the motivating case is start-of-term setup, e.g. `LEC 01`–`LEC 10` due weekly. Toggled inline from the existing single-task add row (no modal, no new route/view) since it's used rarely (a few times a term) and shouldn't add permanent weight to the everyday single-add flow.

**Name generation:** no template syntax. The typed starting name has its trailing number auto-detected via a `\d+$` match, preserving zero-padding width (`LEC 01` → prefix `"LEC "`, width `2`, start `1`); each subsequent task increments that number (`LEC 02`, `LEC 03`, …). If the name has no trailing number, fall back to appending `" 2"`, `" 3"`, etc.

**Due dates:** `due_i = start_due + i * interval_days` for `i` in `range(count)`. No catch-up/skip logic — if a computed date is invalid it's just a plain date.

**Skipping an occurrence** (e.g. week 6) is not a feature — generate the full run, delete the unwanted task manually afterward.

###### Backend

- [x] `server/services/tasks.py` — `add_task_series(list_name, base_name, start_due, interval_days, count, email=None, tz_name="UTC")`: validates inputs (`count` positive, reasonable upper bound e.g. 100, `interval_days` positive), derives the name sequence via the trailing-number regex described above, computes due dates by adding `interval_days * i` to `start_due`, and appends all `count` tasks in a single `db.load`/`db.save` (not a loop over `add_task`, to avoid `count` separate file writes).
- [x] `server/api.py` — `POST /api/add-series` — accepts `{ list, name, startDue, intervalDays, count }`; delegates to `add_task_series`; requires auth.

###### Backend — tests

- [x] `server/tests/test_tasks.py` — test name sequence generation (padding preserved, e.g. `LEC 01` → `LEC 01..LEC 10`; no trailing number falls back to `" 2"`, `" 3"`, …); test due date spacing; test rejection of non-positive `count`/`interval_days`; test unknown list.
- [x] `server/tests/test_api.py` — test `POST /api/add-series` end-to-end (task count, names, due dates all correct in the saved DB).

###### Frontend

- [x] `client/src/lib/api.ts` — add `addSeries: '/api/add-series'` to the `API` const object.
- [x] `client/src/components/tasks/AddTaskForm.tsx` — add `mode: 'single' | 'batch'` state; a small toggle button as the leftmost element of the row flips it. Batch mode reuses the existing name input as the starting name and the existing date input as the start date, and adds two `type="number"` inputs (interval in days, default 7; count). `submit()` branches: single mode calls `API.add` as today, batch mode calls `API.addSeries`.
- [x] `client/src/components/tasks/Tasks.module.css` — `.inlineAdd` gets `flex-wrap: wrap` so the row reflows to multiple lines by available width rather than fixed breakpoints (looks like 2 rows at normal width, folds further on narrow viewports); the interval/count number inputs are self-bordered chips (`.inlineAddNumber`, own border/radius) rather than continuing the `border-right`-divider chain, so there's no dangling divider regardless of where a line wraps.

###### Frontend — verification

- [x] `cd client && npm run lint`
- [x] `cd client && npm run build`
- [ ] Manual: toggle batch mode, generate a series, confirm names/dates/count are correct; confirm the row wraps sensibly at normal width and at mobile width; confirm toggling back to single mode restores the normal add flow. (Not verified this session — the app requires real Google OAuth login with no local bypass, and no browser tool was available to drive it; needs a manual pass.)

##### Milestone 11 — Recurring Tasks

A task can recur: on completion it logs to the daysheet as usual, but it never enters the done list — the completed occurrence is deleted and replaced by a fresh task row for the next occurrence (same name and list, new id, due date set to the prior occurrence's own due date plus the interval — falling back to today only if it had no due date — no catch-up/skip logic). Because each occurrence is deleted on completion, there's no "already done" state to undo (beyond deleting the daysheet entry) and no way to re-complete the same occurrence — the id is simply gone, so a repeat attempt fails with "not found" rather than needing a special same-day guard. Recurrence is created via a special mode of the existing batch-add row rather than a separate flow, since a recurring task is conceptually "batch add with unlimited entries" — generated lazily, one occurrence at a time, instead of all upfront.

Updated task schema:

```json
{ "id": "uuid", "name": "Water plants", "listId": "uuid", "due": "2026-04-30 | null", "doneAt": null, "description": "", "flagged": false, "recurIntervalDays": "7 | null" }
```

###### Backend

- [x] `server/services/tasks.py` — `add_task` gains an optional `recur_interval_days` param, validated as a positive int when given; sets `recurIntervalDays` on new tasks (`null` when not recurring).
- [x] `server/services/tasks.py` — `edit_task` gains `recur_interval_days` / `update_recur` params, following the same shape as the existing `due` / `update_due` pair, so the interval can be set, changed, or cleared independently of renaming.
- [x] `server/services/tasks.py` — `duplicate_task` copies `recurIntervalDays` onto the copy (unlike `flagged`, which resets).
- [x] `server/services/tasks.py` — `done_task` always logs the `DONE` daysheet entry first. If `recurIntervalDays` is set, it deletes the completed task row and appends a new one (new id, same name/list/`recurIntervalDays`, `due = (task's own due, or today if it had none) + recurIntervalDays`, `doneAt: null`) instead of setting `doneAt`; otherwise it behaves as before (`doneAt` set, `flagged` cleared). Basing the new due date on the completed occurrence's own due date (not `today`) matters because completing several occurrences back-to-back on the same real-world day must still advance the due date each time. Since the completed occurrence's id no longer exists afterward, no same-day completion guard is needed — a repeat attempt on the same id fails with "not found," and it can't collide with a different task of the same name.
- [x] `server/api.py` — `POST /api/add` and `POST /api/edit` pass `recurIntervalDays` (and `"recurIntervalDays" in body` as the edit update-flag) through to the services above.
- [x] `server/api.py` — `GET /api/state` normalizes `recurIntervalDays` with `t.get("recurIntervalDays")` for backward compatibility with existing records.
- [x] `server/services/tasks.py` — the "delete completed row, spawn a next-occurrence row" logic is factored into a shared `_replace_with_next_occurrence(data, task, today)` helper, used by both `done_task` and the new `skip_task`.
- [x] `server/services/tasks.py` — `skip_task(task_id, email=None, tz_name="UTC")`: rejects non-recurring tasks, otherwise calls `_replace_with_next_occurrence` without logging any daysheet entry (skipping isn't a completion, so it leaves no daysheet trace).
- [x] `server/api.py` — `POST /api/skip-task` — accepts `{ taskId }`; delegates to `skip_task`; requires auth.

###### Backend — tests

- [x] `server/tests/test_tasks.py` — `add_task` sets/validates `recurIntervalDays`; `edit_task` sets/clears/preserves it; `duplicate_task` copies it; `done_task` replaces a recurring task with a next-occurrence row (due date rolled forward from the prior due date, original id gone) instead of marking it done, bases the new due date on the prior due date rather than today (so completing several occurrences same-day still advances each time), falls back to today when the task had no due date, does not spawn one for a plain task, rejects re-completing the same (now-deleted) occurrence with "not found," and allows completing two distinct same-named tasks on the same day; `skip_task` replaces a recurring task with a next-occurrence row without logging a daysheet entry, and rejects non-recurring/unknown tasks.
- [x] `server/tests/test_api.py` — end-to-end coverage for `/api/add`, `/api/edit` with `recurIntervalDays`, `/api/state` normalization for legacy records, and `/api/skip-task`.

###### Frontend

- [x] `client/src/lib/types.ts` — add `recurIntervalDays: number | null` to `Task`.
- [x] `client/src/components/icons.tsx` — add `RepeatIcon`, an infinity symbol (two overlapping circles), used as both the recurring-task indicator and the batch-mode recurring toggle.
- [x] `client/src/components/tasks/TaskRow.tsx` — display mode: when `task.description` and/or `task.recurIntervalDays` are set, both icons render stacked (repeat above note) inside one `.taskIcons` container next to the task name, rather than laid out inline. Edit mode: only for already-recurring tasks, a `↻`-labelled (interval glyph, not the infinity icon) number input sits next to the due-date input, wired through `edit_task`'s `recurIntervalDays` / update-flag the same way the due-date input already works; empty clears the interval. Recurrence itself can't be created from the edit row — only via the batch-add toggle.
- [x] `client/src/components/tasks/AddTaskForm.tsx` — batch mode gains a `RepeatIcon` toggle after the count input; when active, the count input is disabled and `submit()` calls `API.add` with `recurIntervalDays` set (a single recurring task) instead of `API.addSeries` (a fixed batch of distinct tasks).
- [x] `client/src/components/tasks/Tasks.module.css` — `.taskIcons` (stacks the note/repeat icons vertically), `.taskEditRecurGroup` / `.taskEditRecur` (bordered chip that grows full-width in card/group view's stacked edit row, fixed small width in focused view, matching `.taskEditDue`'s treatment), `.inlineAddRecurToggle` (icon-only toggle button); the divider before it falls out of generalizing `.inlineAddSeriesGroup:first-child` to `:not(:last-child)` rather than a one-off border on the toggle itself.
- [x] `client/src/components/icons.tsx` — add `SkipIcon` (a right-pointing triangle + bar, the media-player "skip" glyph), distinct from `ContinueIcon`'s double-chevron.
- [x] `client/src/lib/api.ts` — add `skipTask: '/api/skip-task'` to the `API` const object.
- [x] `client/src/components/tasks/TaskRow.tsx` — a third `taskLeft` button, `SkipIcon`, shown only when `!task.doneAt && task.recurIntervalDays` (so non-recurring rows are unaffected and stay the same height); behind a `confirm()` dialog like delete, calls `act(API.skipTask, { taskId: task.id })`.
- [x] `client/src/action-button.css` — `.action-btn.skp:hover` (accent color, matching `.pin`'s treatment) for the new button.

###### Frontend — verification

- [x] `cd client && npm run lint`
- [x] `cd client && npm run build`
- [ ] Manual: create a recurring task via batch mode's `∞`-style toggle, complete it, confirm it does NOT appear in the done list and instead a new pending task appears with due date rolled forward by the interval and a daysheet entry logged; confirm the repeat icon shows on the new occurrence; edit an existing task's interval via the edit row and confirm it takes effect on its next completion; duplicate a recurring task and confirm the copy keeps the interval; confirm two same-named tasks can each be completed independently on the same day; confirm the skip button only appears on recurring, non-done rows, confirms before acting, and advances the due date without logging a daysheet entry. (Not verified this session — the app requires real Google OAuth login with no local bypass, and no browser tool was available to drive it; needs a manual pass.)

##### Milestone 12 — Description Checklists

Markdown-style checkboxes inside a task's description, with a matching progress indicator on the task row. No schema change — descriptions remain a plain text field; checkbox state is encoded in the text itself as GitHub-style `- [ ]` / `- [x]` lines.

###### Frontend

- [x] `client/src/lib/utils.ts` — shared `CHECKBOX_LINE` regex (`- [ ] text` / `- [x] text`, case-insensitive mark, leading indentation captured) and `checkboxProgress(description)` helper returning `{ done, total } | null`.
- [x] `client/src/components/tasks/TaskDetail.tsx` — the read-only description view (shown when not editing) renders checkbox lines as live `<input type="checkbox">` elements instead of plain text; clicking one flips `[ ]`/`[x]` in the underlying description text and saves through the existing 600ms-debounced autosave. Edit mode (the raw textarea) is unaffected — checkboxes only render in the read-only view, matching how URL-linkification already only applies there.
- [x] `client/src/components/tasks/TaskRow.tsx` / `Tasks.module.css` — a task row whose description contains checkboxes shows a thin `--accent` bar flush against its right edge (mirroring the flagged left border), filling bottom-to-top proportional to checked/total via a hard-stop `linear-gradient`; `.taskRow` clips it (`overflow: hidden`) so it respects the row's rounded corners instead of overhanging them.

###### Frontend — verification

- [x] `cd client && npm run lint`
- [x] `cd client && npm run build`
- [ ] Manual: add `- [ ] ...` lines to a description, confirm they render as checkboxes only outside edit mode; click to check/uncheck and confirm the state persists after a refresh; confirm the row's right-edge progress bar fills correctly and stays clipped to the row's corners at 0%, partial, and 100% completion.

##### Future

- Daysheet analytics
- Turn a task description into an actionable checklist (AI)
- Screen Mates
