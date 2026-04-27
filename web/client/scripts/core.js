export const state = {
  view: 'tasks',
  filter: 'all',
  selectedList: null,
  selectedGroup: null,
  data: null,
  daysheet: null,
  daysheetDate: todayStr(),
  calendarUrl: '',
  showDone: new Set(),
  expandedCards: new Set(),
};

export function todayStr() {
  return new Date().toISOString().slice(0, 10);
}

// ── DOM helpers ──

export function el(tag, props, ...children) {
  const node = document.createElement(tag);
  if (props) {
    for (const [k, v] of Object.entries(props)) {
      if (k === 'class') node.className = v;
      else if (k === 'on') Object.entries(v).forEach(([e, fn]) => node.addEventListener(e, fn));
      else if (k in node) node[k] = v;
      else node.setAttribute(k, v);
    }
  }
  for (const c of children.flat(Infinity)) {
    if (c == null || c === false) continue;
    node.append(c.nodeType ? c : document.createTextNode(String(c)));
  }
  return node;
}

export function icon(d, size = 12) {
  const ns = 'http://www.w3.org/2000/svg';
  const svg = document.createElementNS(ns, 'svg');
  svg.setAttribute('width', size); svg.setAttribute('height', size);
  svg.setAttribute('viewBox', '0 0 16 16'); svg.setAttribute('fill', 'none');
  svg.setAttribute('stroke', 'currentColor'); svg.setAttribute('stroke-width', '1.8');
  svg.setAttribute('stroke-linecap', 'round'); svg.setAttribute('stroke-linejoin', 'round');
  svg.innerHTML = d;
  return svg;
}

// ── Constants ──

export const MSG = {
  noTasks:    'No tasks',
  noEntries:  'No entries',
  addTask:    'Add task…',
  entryText:  'Entry text…',
  listName:   'List name…',
  newList:    '+ New List',
  today:      'Today',
  yesterday:  'Yesterday',
  daysheet:   'Daysheet',
  tasks:      'Tasks',
  others:     'Others',
  calendar:   'Calendar',
  noCalUrl:   'No calendars configured. Add a "calendars" array and "calendarTimezone" to ~/.taskman/config.json.',
};

export const API = {
  config:         '/api/config',
  state:          '/api/state',
  daysheet:       '/api/daysheet',
  add:            '/api/add',
  addList:        '/api/add-list',
  moveTask:       '/api/move-task',
  moveList:       '/api/move-list',
  renameList:     '/api/rename-list',
  deleteList:     '/api/delete-list',
  renameGroup:    '/api/rename-group',
  deleteGroup:    '/api/delete-group',
  done:           '/api/done',
  undo:           '/api/undo',
  delete:         '/api/delete',
  continue:       '/api/continue',
  edit:           '/api/edit',
  log:            '/api/log',
  daysheetDelete: '/api/daysheet/delete',
  daysheetEdit:   '/api/daysheet/edit',
};

export const IC = {
  tasks:    '<rect x="2.5" y="2.5" width="11" height="11" rx="1.5"/><path d="M5.5 8l2 2L10.5 6"/>',
  daysheet: '<path d="M4 2h8a1 1 0 011 1v10a1 1 0 01-1 1H4a1 1 0 01-1-1V3a1 1 0 011-1z"/><path d="M6 6h4M6 9h4M6 12h2"/>',
  check:    '<path d="M3 8.5l3 3L13 5"/>',
  undo:     '<path d="M4 7H10a3 3 0 010 6H8"/><path d="M4 4L1 7l3 3"/>',
  delete:   '<path d="M3 3l10 10M13 3L3 13"/>',
  continue: '<path d="M4 4l4 4-4 4"/><path d="M9 4l4 4-4 4"/>',
  chevL:    '<path d="M10 12L6 8l4-4"/>',
  chevR:    '<path d="M6 4l4 4-4 4"/>',
  plus:     '<path d="M8 3v10M3 8h10"/>',
  edit:     '<path d="M12 2l2 2-9 9-3 1 1-3 9-9z"/>',
  move:     '<path d="M3 8h10M9 4l4 4-4 4"/>',
};

// ── Network ──

export async function api(method, path, body) {
  const opts = { method };
  if (body != null) {
    opts.headers = { 'Content-Type': 'application/json' };
    opts.body = JSON.stringify(body);
  }
  try {
    const res = await fetch(path, opts);
    const json = await res.json();
    if (!res.ok) { console.log(json.message || json.error || 'Request failed'); return null; }
    return json;
  } catch { console.log('Request failed'); return null; }
}

// render() is defined in app.js; registered here to avoid a circular import
let _render = () => {};
export function registerRender(fn) { _render = fn; }

export async function refresh() {
  if (state.view === 'daysheet') {
    const [ds, data] = await Promise.all([
      api('GET', `${API.daysheet}?date=${state.daysheetDate}`),
      state.data ? Promise.resolve(state.data) : api('GET', API.state),
    ]);
    state.daysheet = ds;
    state.data = data;
  } else {
    state.data = await api('GET', API.state);
  }
  _render();
}

export async function act(path, body) {
  const res = await api('POST', path, body);
  if (res?.ok) {
    state.data = null;
    state.daysheet = null;
    await refresh();
  }
}

// ── Data helpers ──

export function sortByName(arr) {
  return [...arr].sort((a, b) => {
    if (/^others?$/i.test(a.name)) return 1;
    if (/^others?$/i.test(b.name)) return -1;
    return a.name.localeCompare(b.name);
  });
}

export function pendingFor(listId) {
  const { tasks, today } = state.data;
  const todayD = new Date(today);
  const pending = tasks.filter(t => t.listId === listId && !t.done);
  const byDueThenName = (a, b) => a.due.localeCompare(b.due) || a.name.localeCompare(b.name);
  if (state.filter === 'day') {
    return pending.filter(t => t.due && new Date(t.due) <= todayD).sort(byDueThenName);
  }
  if (state.filter === 'week') {
    const cut = new Date(todayD); cut.setDate(cut.getDate() + 7);
    return pending.filter(t => t.due && new Date(t.due) <= cut).sort(byDueThenName);
  }
  return [
    ...pending.filter(t => t.due).sort(byDueThenName),
    ...pending.filter(t => !t.due).sort((a, b) => a.name.localeCompare(b.name)),
  ];
}

export function doneFor(listId) {
  return state.data.tasks
    .filter(t => t.listId === listId && t.done)
    .sort((a, b) => b.done.localeCompare(a.done));
}

export function formatDue(due) {
  const today = state.data.today;
  const dueD = new Date(due);
  const todayD = new Date(today);
  const days = Math.round((dueD - todayD) / 86400000);
  if (days < 0)  return { label: dueD.toLocaleDateString(undefined, { month: 'short', day: 'numeric' }), cls: 'overdue' };
  if (days === 0) return { label: 'today', cls: 'today-due' };
  if (days === 1) return { label: 'tomorrow', cls: 'soon' };
  if (days < 7)  return { label: dueD.toLocaleDateString(undefined, { weekday: 'short' }).toLowerCase(), cls: '' };
  return { label: dueD.toLocaleDateString(undefined, { month: 'short', day: 'numeric' }), cls: '' };
}

export function inlineAdd(listName, onAdd) {
  const nameIn = el('input', { type: 'text', placeholder: MSG.addTask });
  const dueIn  = el('input', { type: 'date' });
  const submit = () => {
    const name = nameIn.value.trim();
    if (!name) return;
    onAdd(listName, name, dueIn.value || null);
    nameIn.value = ''; dueIn.value = '';
  };
  nameIn.addEventListener('keydown', e => e.key === 'Enter' && submit());
  return { nameIn, dueIn, submit };
}
