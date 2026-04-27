# Taskman

A minimal web-based task manager for personal daily use. Tasks live in lists, lists can be grouped, and everything is stored in a flat JSON file at `~/.taskman/db.json`.

---

## Setup

```bash
pip install flask
```

```bash
cd client && npm install && npm run build
```

---

## Running

```bash
flask --app server run -p 5050
```

This starts the Flask API at `http://127.0.0.1:5050`.

```bash
flask --app server run -p 8080 --debug
```

For frontend development, run both in parallel:

```bash
flask --app server run -p 5050
cd client && npm run dev
```

The Flask server only exposes `/api` routes. It does not currently serve the frontend bundle.

---

## Frontend Structure

The client is organized by role:

- `client/src/views/` contains route-level screens:
  - `CardsView.tsx` for `/tasks`
  - `FocusedView.tsx` for `/list/:listId`
  - `DaysheetView.tsx` for `/daysheet`
  - `CalendarView.tsx` for `/calendar`
- `client/src/components/` contains reusable UI:
  - `Sidebar/` for sidebar-specific pieces
  - `tasks/` for reusable task UI like `TaskRow`, `TaskCard`, `TaskDetail`, and `AddTaskForm`
- `client/src/hooks/` contains app-level hooks like `useAppData`
- `client/src/lib/` contains shared API/types/utilities

Styling is split between:

- `client/style.css` for global tokens, themes, reset, and app-wide layout
- CSS Modules for component/view-local styles
- `client/src/action-button.css` for the shared global `.action-btn` action button primitive

---

## Task Descriptions

Click any task row to open a detail panel. The panel shows the task's list and due date, and provides a freeform text area for notes. Changes are auto-saved with a short debounce. Raw URLs in the description are rendered as clickable links.

On wide screens the panel slides in alongside the task list. On mobile it replaces the main content. Press Escape or the ✕ button to close.

---

## Calendar Config

Create `~/.taskman/config.json` to configure which calendars appear in the embedded Google Calendar view:

```json
{
  "calendars": [
    { "id": "you@gmail.com", "color": "#B39DDB" },
    { "id": "other@group.calendar.google.com", "color": "#E67C73" }
  ],
  "calendarTimezone": "America/Sydney"
}
```

Available colors: `#E67C73` Flamingo · `#33B679` Sage · `#B39DDB` Wisteria · `#039BE5` Peacock · `#3F51B5` Blueberry · `#7986CB` Lavender · `#8E24AA` Grape · `#F6BF26` Banana · `#F4511E` Tangerine · `#0B8043` Basil · `#D50000` Tomato · `#616161` Graphite
