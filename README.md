# Taskman

A minimal web-based task manager for personal daily use. Tasks live in lists, lists can be grouped, and everything is stored in a flat JSON file at `~/.taskman/db.json`.

---

## Setup

```bash
pip install -r requirements.txt
```

```bash
cd client && npm install && npm run build
```

Create a `.env` file in the project root with your Google OAuth credentials:

```
GOOGLE_CLIENT_ID=your-client-id
GOOGLE_CLIENT_SECRET=your-client-secret
```

---

## Running

```bash
flask --app server run -p 5050
```

This starts the Flask API at `http://127.0.0.1:5050`.

For frontend development, run both in parallel:

```bash
flask --app server run -p 5050
cd client && npm run dev
```

The Flask server only exposes `/api` routes. It does not serve the frontend bundle.

---

## Authentication

Taskman uses Google OAuth as the sole login method. On first visit you are redirected to `/login` and prompted to sign in with Google. The OAuth flow also retrieves a refresh token used for calendar auto-discovery.

To set up:

1. Create a Google Cloud project and enable the **Google Calendar API** and **Google+ API** (for userinfo).
2. Create an OAuth 2.0 credential (Web application) and add `http://127.0.0.1:5050/api/oauth/callback` as an authorised redirect URI.
3. Copy the client ID and secret into `.env` as shown above.

---

## Frontend Structure

The client is organized by role:

- `client/src/views/` contains route-level screens:
  - `CardsView.tsx` for `/tasks`
  - `FocusedView.tsx` for `/list/:listId`
  - `DaysheetView.tsx` for `/daysheet`
  - `CalendarView.tsx` for `/calendar`
  - `LoginView.tsx` for `/login`
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

## Calendar

After signing in, your Google calendars are auto-discovered and shown in the embedded calendar view. The first five calendars are assigned preset colors automatically.

To override colors or restrict which calendars appear, add a `calendars` key to `~/.taskman/config.json`:

```json
{
  "calendars": [
    { "id": "you@gmail.com", "color": "#B39DDB" },
    { "id": "other@group.calendar.google.com", "color": "#E67C73" }
  ],
  "calendarTimezone": "America/Sydney"
}
```

Available embed colors: `#E67C73` Flamingo · `#33B679` Sage · `#B39DDB` Wisteria · `#039BE5` Peacock · `#3F51B5` Blueberry · `#7986CB` Lavender · `#8E24AA` Grape · `#F6BF26` Banana · `#F4511E` Tangerine · `#0B8043` Basil · `#D50000` Tomato · `#616161` Graphite
