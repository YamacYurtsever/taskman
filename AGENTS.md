# Taskman

A minimal web-based task manager built for personal daily use. Tasks are organized into lists, and lists can be optionally grouped. Each task has a name, a parent list, and an optional due date. Data is stored in a flat JSON file at `~/.taskman/db.json`.

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
    db.py               JSON persistence (~/.taskman/db.json)
    config.py           Config loader (~/.taskman/config.json)
    constants.py        Shared constants and DaysheetEntryType
    tests/              Pytest test suite
      test_api.py       Flask route tests
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
      views/            Route-level screens: CalendarView, DaysheetView, CardsView, FocusedView
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
- `server/db.py` creates `~/.taskman/db.json` from `EMPTY_DB` if missing and resets to `EMPTY_DB` if the JSON is corrupt.
- `server/config.py` creates `~/.taskman/config.json` from defaults if missing, then overlays stored values onto defaults.
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

---

### Database Schema

```json
{
  "groups":   [{ "id": "uuid", "name": "UNSW" }],
  "lists":    [{ "id": "uuid", "name": "COMP3131", "groupId": "uuid | null" }],
  "tasks":    [{ "id": "uuid", "name": "Finish Assignment 5", "listId": "uuid", "due": "2026-04-30 | null", "done": "2026-04-26 | null", "description": "" }],
  "daysheet": [{ "id": "uuid", "datetime": "2026-04-26T14:32:05", "listId": "uuid", "type": "log | continue | done", "text": "Talked with Baba" }]
}
```

---

### Tech Stack

- **Backend:** Python, Flask
- **Frontend:** Vite + React + TypeScript, React Router
- **Styling:** CSS Modules + global `client/style.css` + shared `client/src/action-button.css`
- **Storage:** JSON flat file (`~/.taskman/db.json`)
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
- [x] Add / mark done / undo / delete / rename / move tasks
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

##### Milestone 5 — Authentication

- [ ] User/account model supporting local single-user and future hosted deployment
- [ ] Web auth flow: login, logout, session handling
- [ ] All API endpoints protected when auth is enabled
- [ ] Auth config: mode, secrets, redirect URLs (no committed secrets)
- [ ] OAuth provider support with token refresh
- [ ] Google OAuth: pull the user's calendars automatically, replacing the manual `config.json` calendar list
- [ ] Account/settings UI for managing connected providers and calendar selection
- [ ] Persistence boundaries ready for a deployed database

##### Milestone 6 — Deploy

- [ ] Gunicorn as the production WSGI server instead of Flask dev server
- [ ] Dockerfile — single container running Gunicorn, serving both the API and built frontend static files
- [ ] Deploy to Fly.io — one app, one shared-CPU VM, one persistent volume
- [ ] `DB_PATH` driven by environment variable; `db.json` stored on the Fly volume (not `~/.taskman/`)
- [ ] Health check endpoint (`/api/health`) for Fly's built-in health monitoring
- [ ] Automated backups: periodic copy of `db.json` to a private GitHub repo or Cloudflare R2
- [ ] CI pipeline extended to build and deploy to Fly on release
