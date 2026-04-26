'use strict';

// ─────────────────────────── State ────────────────────────────

const state = {
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

function todayStr() {
  return new Date().toISOString().slice(0, 10);
}

// ──────────────────────── DOM helpers ─────────────────────────

function el(tag, props, ...children) {
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

function icon(d, size = 13) {
  const ns = 'http://www.w3.org/2000/svg';
  const svg = document.createElementNS(ns, 'svg');
  svg.setAttribute('width', size); svg.setAttribute('height', size);
  svg.setAttribute('viewBox', '0 0 16 16'); svg.setAttribute('fill', 'none');
  svg.setAttribute('stroke', 'currentColor'); svg.setAttribute('stroke-width', '1.8');
  svg.setAttribute('stroke-linecap', 'round'); svg.setAttribute('stroke-linejoin', 'round');
  svg.innerHTML = d;
  return svg;
}

const MSG = {
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

const API = {
  config:         '/api/config',
  state:          '/api/state',
  daysheet:       '/api/daysheet',
  add:            '/api/add',
  addList:        '/api/add-list',
  done:           '/api/done',
  undo:           '/api/undo',
  delete:         '/api/delete',
  continue:       '/api/continue',
  log:            '/api/log',
  daysheetDelete: '/api/daysheet/delete',
};

const IC = {
  tasks:    '<rect x="2.5" y="2.5" width="11" height="11" rx="1.5"/><path d="M5.5 8l2 2L10.5 6"/>',
  daysheet: '<path d="M4 2h8a1 1 0 011 1v10a1 1 0 01-1 1H4a1 1 0 01-1-1V3a1 1 0 011-1z"/><path d="M6 6h4M6 9h4M6 12h2"/>',
  check:    '<path d="M3 8.5l3 3L13 5"/>',
  undo:     '<path d="M4 7H10a3 3 0 010 6H8"/><path d="M4 4L1 7l3 3"/>',
  delete:   '<path d="M3 3l10 10M13 3L3 13"/>',
  continue: '<path d="M4 4l4 4-4 4"/><path d="M9 4l4 4-4 4"/>',
  chevL:    '<path d="M10 12L6 8l4-4"/>',
  chevR:    '<path d="M6 4l4 4-4 4"/>',
  plus:     '<path d="M8 3v10M3 8h10"/>',
};

// ──────────────────────────── API ─────────────────────────────

async function api(method, path, body) {
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

async function refresh() {
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
  render();
  renderSidebar();
}

async function act(path, body, msg) {
  const res = await api('POST', path, body);
  if (res?.ok) {
    state.data = null;
    state.daysheet = null;
    await refresh();
  }
}

function sortByName(arr) {
  return [...arr].sort((a, b) => {
    if (/^others?$/i.test(a.name)) return 1;
    if (/^others?$/i.test(b.name)) return -1;
    return a.name.localeCompare(b.name);
  });
}

// ──────────────────────── Data helpers ────────────────────────

function pendingFor(listId) {
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

function doneFor(listId) {
  return state.data.tasks
    .filter(t => t.listId === listId && t.done)
    .sort((a, b) => b.done.localeCompare(a.done));
}

function formatDue(due) {
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

// ────────────────────────── Sidebar ───────────────────────────

function renderSidebar() {
  const nav = document.getElementById('list-nav');
  nav.replaceChildren();
  if (!state.data) return;
  const { groups, lists } = state.data;

  function listBtn(list) {
    const count = pendingFor(list.id).length;
    const active = state.view === 'tasks' && state.selectedList === list.id;
    return el('button', {
      class: 'list-nav-item nav-list' + (active ? ' active' : ''),
      on: { click: () => { state.selectedList = list.id; state.selectedGroup = null; state.view = 'tasks'; render(); renderSidebar(); } },
    }, list.name, count ? el('span', { class: 'lni-count' }, count) : null);
  }

  // Top-level: Calendar
  const calActive = state.view === 'calendar';
  nav.append(el('button', {
    class: 'list-nav-item nav-top' + (calActive ? ' active' : ''),
    on: { click: () => { state.view = 'calendar'; state.selectedList = null; state.selectedGroup = null; render(); } },
  }, MSG.calendar));

  // Top-level: Daysheet
  const dsActive = state.view === 'daysheet';
  nav.append(el('button', {
    class: 'list-nav-item nav-top' + (dsActive ? ' active' : ''),
    on: { click: () => { state.view = 'daysheet'; state.selectedList = null; state.selectedGroup = null; refresh(); } },
  }, MSG.daysheet));

  // Tasks section
  const tasksActive = state.view === 'tasks' && state.selectedList === null && state.selectedGroup === null;
  const tasksHeader = el('button', {
    class: 'list-nav-item nav-top' + (tasksActive ? ' active' : ''),
    on: { click: () => { state.selectedList = null; state.selectedGroup = null; state.view = 'tasks'; render(); renderSidebar(); } },
  }, MSG.tasks);

  const tasksSectionBody = el('div', { class: 'nav-section-body' });
  const seen = new Set();

  for (const g of sortByName(groups)) {
    const gl = sortByName(lists.filter(l => l.groupId === g.id));
    if (!gl.length) continue;
    const grpActive = state.view === 'tasks' && state.selectedGroup === g.id;
    const groupHeader = el('button', {
      class: 'list-nav-item nav-group-header' + (grpActive ? ' active' : ''),
      on: { click: () => { state.selectedGroup = g.id; state.selectedList = null; state.view = 'tasks'; render(); renderSidebar(); } },
    }, g.name);
    const groupLists = el('div', { class: 'nav-group-lists' }, ...gl.map(listBtn));
    tasksSectionBody.append(el('div', { class: 'nav-group' }, groupHeader, groupLists));
    gl.forEach(l => seen.add(l.id));
  }

  const ungrouped = sortByName(lists.filter(l => !seen.has(l.id)));
  ungrouped.forEach(l => tasksSectionBody.append(listBtn(l)));

  // New List input
  const inputRow = el('div', { class: 'new-list-input hidden' });
  const input = el('input', { type: 'text', placeholder: MSG.listName, autocomplete: 'off' });
  const submit = async () => {
    const name = input.value.trim();
    if (!name) return;
    input.value = '';
    inputRow.classList.add('hidden');
    await act(API.addList, { list: name });
  };
  input.addEventListener('keydown', e => {
    if (e.key === 'Enter') submit();
    if (e.key === 'Escape') { input.value = ''; inputRow.classList.add('hidden'); }
  });
  input.addEventListener('blur', () => { if (!input.value.trim()) inputRow.classList.add('hidden'); });
  inputRow.append(input);
  tasksSectionBody.append(inputRow);
  tasksSectionBody.append(el('button', {
    class: 'new-list-btn',
    on: { click: () => { inputRow.classList.remove('hidden'); input.focus(); } },
  }, MSG.newList));

  nav.append(el('div', { class: 'nav-section' }, tasksHeader, tasksSectionBody));
}

// ────────────────────────── Task row ──────────────────────────

function taskRow(task, listName) {
  const due = task.due ? formatDue(task.due) : null;

  const checkEl = el('div', {
    class: 'task-check',
    title: task.done ? 'Mark pending' : 'Mark done',
    on: {
      click: () => task.done
        ? act(API.undo, { list: listName, name: task.name })
        : act(API.done, { list: listName, name: task.name }, `✓ ${task.name}`),
    },
  },
    el('svg', { class: 'task-check-svg', width: '9', height: '9', viewBox: '0 0 16 16',
      fill: 'none', stroke: '#fff', 'stroke-width': '2.5',
      'stroke-linecap': 'round', 'stroke-linejoin': 'round' },
      el('path', { d: 'M3 8.5l3 3L13 5' })),
  );

  const dueEl = due ? el('span', { class: 'task-due' + (due.cls ? ' ' + due.cls : '') }, due.label) : null;

  const continueEl = task.done
    ? null
    : el('button', { class: 'task-btn cnt', title: 'Log continue',
        on: { click: () => act(API.continue, { list: listName, task: task.name }) } },
        icon(IC.continue, 11));

  const deleteBtn = el('button', { class: 'task-btn del', title: 'Delete',
    on: { click: () => { if (confirm(`Delete "${task.name}"?`)) act(API.delete, { list: listName, name: task.name }); } } },
    icon(IC.delete, 11));

  return el('div', { class: 'task-row' + (task.done ? ' done' : '') },
    el('div', { class: 'task-left' }, checkEl, continueEl),
    el('div', { class: 'task-body' },
      el('span', { class: 'task-name' }, task.name),
      dueEl,
    ),
    el('div', { class: 'task-right' }, deleteBtn),
  );
}

// ─────────────────────── Inline add row ───────────────────────

function inlineAdd(listName, onAdd) {
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

// ─────────────────── Cards view (all lists) ───────────────────

const CARD_LIMIT = 10;

function renderCard(list) {
  const pending = pendingFor(list.id);
  if (!pending.length) return null;

  const expanded = state.expandedCards.has(list.id);
  const overflow = pending.length > CARD_LIMIT;
  const visible = overflow && !expanded ? pending.slice(0, CARD_LIMIT) : pending;

  const body = el('div', { class: 'card-body' },
    ...visible.map(t => taskRow(t, list.name)),
  );

  const toggleBtn = overflow ? el('button', { class: 'card-overflow-toggle',
    on: { click: () => {
      expanded ? state.expandedCards.delete(list.id) : state.expandedCards.add(list.id);
      render();
    }},
  },
    icon(expanded ? IC.chevL : IC.chevR, 10),
    expanded ? ` hide ${pending.length - CARD_LIMIT}` : ` ${pending.length - CARD_LIMIT} more`,
  ) : null;

  const { nameIn, dueIn, submit } = inlineAdd(list.name, (l, n, d) => act(API.add, { list: l, name: n, due: d }));

  return el('div', { class: 'card' },
    el('div', { class: 'card-header',
      on: { click: () => { state.selectedList = list.id; render(); renderSidebar(); } } },
      el('span', { class: 'card-title' }, list.name),
      el('span', { class: 'card-count' }, pending.length),
    ),
    body,
    toggleBtn
  );
}

function renderCardsView() {
  const main = document.getElementById('main');
  main.replaceChildren();
  const { groups, lists } = state.data;

  if (state.selectedGroup) {
    const g = groups.find(x => x.id === state.selectedGroup);
    if (!g) { state.selectedGroup = null; renderCardsView(); return; }
    const gl = sortByName(lists.filter(l => l.groupId === g.id));
    const cards = gl.map(renderCard).filter(Boolean);
    main.append(el('div', { class: 'section-label' }, g.name));
    if (cards.length) {
      main.append(el('div', { class: 'cards-grid' }, ...cards));
    } else {
      main.append(el('div', { class: 'empty' }, MSG.noTasks));
    }
    return;
  }

  const seen = new Set();
  for (const g of sortByName(groups)) {
    const gl = sortByName(lists.filter(l => l.groupId === g.id));
    if (!gl.length) continue;
    const cards = gl.map(renderCard).filter(Boolean);
    if (cards.length) {
      main.append(el('div', { class: 'section-label section-label-link',
        on: { click: () => { state.selectedGroup = g.id; state.selectedList = null; render(); renderSidebar(); } },
      }, g.name));
      main.append(el('div', { class: 'cards-grid' }, ...cards));
    }
    gl.forEach(l => seen.add(l.id));
  }

  const ungrp = sortByName(lists.filter(l => !seen.has(l.id)));
  if (ungrp.length) {
    const cards = ungrp.map(renderCard).filter(Boolean);
    if (cards.length) {
      const hasGroups = groups.some(g => lists.some(l => l.groupId === g.id));
      if (hasGroups) main.append(el('div', { class: 'section-label' }, MSG.others));
      main.append(el('div', { class: 'cards-grid' }, ...cards));
    }
  }

  if (!main.children.length) {
    main.append(el('div', { class: 'empty' }, MSG.noTasks));
  }
}

// ───────────────── Focused view (single list) ─────────────────

function renderFocusedView(listId) {
  const { lists } = state.data;
  const list = lists.find(l => l.id === listId);
  if (!list) { state.selectedList = null; renderCardsView(); return; }

  const main = document.getElementById('main');
  main.replaceChildren();

  const pending = pendingFor(listId);
  const done    = doneFor(listId);
  const showDone = state.showDone.has(listId);

  const doneSection = el('div', { class: 'done-section' });
  const toggleBtn = el('button', { class: 'done-toggle' });
  function applyToggle(open) {
    toggleBtn.replaceChildren(icon(open ? IC.chevL : IC.chevR, 11), ` ${open ? 'hide' : 'show'} done (${done.length})`);
    doneSection.replaceChildren(...(open ? done.map(t => taskRow(t, list.name)) : []));
  }
  applyToggle(showDone);
  toggleBtn.addEventListener('click', () => {
    const next = !state.showDone.has(listId);
    next ? state.showDone.add(listId) : state.showDone.delete(listId);
    applyToggle(next);
  });

  const { nameIn, dueIn, submit } = inlineAdd(list.name, (l, n, d) => act(API.add, { list: l, name: n, due: d }));

  main.append(
    el('div', { class: 'focused-view' },
      el('div', { class: 'focused-header' },
        el('h1', { class: 'focused-title' }, list.name),
        el('span', { class: 'focused-meta' }, `${pending.length}`),
      ),
      el('div', { class: 'focused-tasks' },
        ...(pending.length
          ? pending.map(t => taskRow(t, list.name))
          : [el('div', { class: 'empty' }, MSG.noTasks)]),
      ),
      el('div', { class: 'focused-add' },
        nameIn, dueIn,
        el('button', { class: 'focused-add-btn', on: { click: submit } }, icon(IC.plus, 15)),
      ),
      done.length ? el('div', { class: 'done-wrapper' }, toggleBtn, doneSection) : null,
    ),
  );
}

// ──────────────────────── Calendar view ───────────────────────

function renderCalendarView() {
  const main = document.getElementById('main');
  main.replaceChildren();
  if (!state.calendarUrl) {
    main.append(el('div', { class: 'empty' }, MSG.noCalUrl));
  }
}

// ─────────────────────── Daysheet view ────────────────────────

function renderDaysheetView() {
  const main = document.getElementById('main');
  main.replaceChildren();

  const ds    = state.daysheet || { entries: [], date: state.daysheetDate };
  const lists = state.data?.lists || [];

  function shiftDay(delta) {
    const d = new Date(state.daysheetDate + 'T12:00:00');
    d.setDate(d.getDate() + delta);
    state.daysheetDate = d.toISOString().slice(0, 10);
    state.daysheet = null;
    refresh();
  }

  function dateLabel(str) {
    const today = todayStr();
    if (str === today) return MSG.today;
    const yest = new Date(); yest.setDate(yest.getDate() - 1);
    if (str === yest.toISOString().slice(0, 10)) return MSG.yesterday;
    return new Date(str + 'T12:00:00').toLocaleDateString(undefined, { month: 'short', day: 'numeric' });
  }

  const view = el('div', { class: 'daysheet-view' });

  view.append(
    el('div', { class: 'daysheet-header' },
      el('h1', { class: 'daysheet-title' }, MSG.daysheet),
      el('div', { class: 'date-nav' },
        el('button', { class: 'date-nav-btn', on: { click: () => shiftDay(-1) } }, icon(IC.chevL, 11)),
        el('span', { class: 'date-nav-label' }, dateLabel(state.daysheetDate)),
        el('button', { class: 'date-nav-btn', on: { click: () => shiftDay(1) } }, icon(IC.chevR, 11)),
      ),
    ),
  );

  const timeline = el('div', { class: 'timeline' });

  if (!ds.entries.length) {
    timeline.append(el('div', { class: 'empty' }, MSG.noEntries));
  } else {
    const bySect = new Map();
    for (const e of ds.entries) {
      if (!bySect.has(e.sectionId)) bySect.set(e.sectionId, { name: e.sectionName, inGroup: e.inGroup, items: [] });
      bySect.get(e.sectionId).items.push(e);
    }
    const sections = sortByName([...bySect.values()]);
    for (const { name, inGroup, items } of sections) {
      timeline.append(
        el('div', { class: 'timeline-group' },
          el('div', { class: 'timeline-group-name' }, name),
          ...items.map(e => {
            const listTag = inGroup ? el('span', { class: 'timeline-list-tag' }, e.listName) : null;
            const delBtn = el('button', { class: 'task-btn del timeline-del', title: 'Delete',
              on: { click: () => act(API.daysheetDelete, { id: e.id }) } },
              icon(IC.delete, 11));
            const prefix = e.type === 'done' ? 'Finished ' : e.type === 'continue' ? 'Continued ' : '';
            return el('div', { class: 'timeline-entry' },
              el('span', { class: 'timeline-time' }, e.datetime.slice(11, 16)),
              el('span', { class: 'timeline-text' }, prefix + e.text, listTag),
              delBtn,
            );
          }),
        ),
      );
    }
  }

  view.append(timeline);

  // Log form
  if (lists.length) {
    const logList = el('select', {}, ...sortByName(lists).map(l => el('option', { value: l.name }, l.name)));
    const logText = el('input', { type: 'text', placeholder: MSG.entryText, autocomplete: 'off' });
    const logSubmit = () => {
      if (!logText.value.trim()) return;
      act(API.log, { list: logList.value, text: logText.value.trim() });
      logText.value = '';
    };
    logText.addEventListener('keydown', e => e.key === 'Enter' && logSubmit());

    view.append(
      el('div', { class: 'log-form' },
        logList,
        logText,
        el('button', { class: 'log-form-btn', on: { click: logSubmit } }, icon(IC.plus, 15)),
      ),
    );
  }

  main.append(view);
}

// ─────────────────────────── Topbar ───────────────────────────

function renderTopbar() {
  const bar = document.getElementById('filter-bar');
  bar.replaceChildren();
  if (state.view !== 'tasks') return;
  bar.append(
    el('div', { class: 'filter-pills' },
      ...['all', 'week', 'day'].map(f =>
        el('button', {
          class: 'filter-pill' + (state.filter === f ? ' active' : ''),
          on: { click: () => { state.filter = f; render(); } },
        }, f[0].toUpperCase() + f.slice(1)),
      ),
    ),
  );
}

// ──────────────────────── Main render ─────────────────────────

function render() {
  renderTopbar();
  renderSidebar();
  const isCalendar = state.view === 'calendar';
  const frame = document.getElementById('calendar-frame');
  const main = document.getElementById('main');
  frame.style.display = isCalendar && state.calendarUrl ? 'block' : 'none';
  main.style.display = isCalendar && state.calendarUrl ? 'none' : '';
  if (isCalendar) { renderCalendarView(); return; }
  if (state.view === 'daysheet') { renderDaysheetView(); return; }
  if (!state.data) return;
  if (state.selectedList) renderFocusedView(state.selectedList);
  else renderCardsView();
}

// ──────────────────────────── Boot ────────────────────────────

(async () => {
  const cfg = await api('GET', API.config);
  if (cfg) {
    state.calendarUrl = cfg.calendarUrl || '';
    if (state.calendarUrl) {
      document.getElementById('calendar-frame').src = state.calendarUrl;
    }
  }
  await refresh();
})();
