const state = {
  view: 'tasks',
  taskFilter: 'all',
  data: null,
  daysheet: null,
  daysheetDate: new Date().toISOString().slice(0, 10),
  showDone: new Set(),
};

const main = document.getElementById('main');
const toast = document.getElementById('toast');

function el(tag, props = {}, ...children) {
  const node = document.createElement(tag);
  for (const [k, v] of Object.entries(props)) {
    if (k === 'class') node.className = v;
    else if (k === 'on') for (const [evt, fn] of Object.entries(v)) node.addEventListener(evt, fn);
    else if (k in node) node[k] = v;
    else node.setAttribute(k, v);
  }
  for (const c of children.flat()) {
    if (c == null || c === false) continue;
    node.append(c.nodeType ? c : document.createTextNode(c));
  }
  return node;
}

let toastTimer;
function showToast(msg, isError = false) {
  if (!msg) return;
  toast.textContent = msg;
  toast.className = 'show' + (isError ? ' error' : '');
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => (toast.className = ''), 2200);
}

async function api(method, path, body) {
  const opts = { method };
  if (body != null) {
    opts.headers = { 'Content-Type': 'application/json' };
    opts.body = JSON.stringify(body);
  }
  try {
    const res = await fetch(path, opts);
    const json = await res.json();
    if (!res.ok) {
      showToast(json.message || json.error || 'Request failed', true);
      return null;
    }
    return json;
  } catch (e) {
    showToast('Request failed', true);
    return null;
  }
}

async function refresh() {
  if (state.view === 'daysheet') {
    state.daysheet = await api('GET', `/api/daysheet?date=${state.daysheetDate}`);
    if (!state.data) state.data = await api('GET', '/api/state');
  } else {
    state.data = await api('GET', '/api/state');
  }
  render();
}

async function action(path, body, successMsg) {
  const res = await api('POST', path, body);
  if (res && res.ok) {
    if (successMsg) showToast(successMsg);
    state.data = null;
    state.daysheet = null;
    await refresh();
  }
}

function filterPending(tasks, listId, mode, today) {
  const todayD = new Date(today);
  const pending = tasks.filter(t => t.listId === listId && !t.done);
  if (mode === 'today') {
    return pending.filter(t => t.due && new Date(t.due) <= todayD)
                  .sort((a, b) => a.due.localeCompare(b.due));
  }
  if (mode === 'week') {
    const cutoff = new Date(todayD); cutoff.setDate(cutoff.getDate() + 7);
    return pending.filter(t => t.due && new Date(t.due) <= cutoff)
                  .sort((a, b) => a.due.localeCompare(b.due));
  }
  const dated = pending.filter(t => t.due).sort((a, b) => a.due.localeCompare(b.due));
  const dateless = pending.filter(t => !t.due);
  return [...dated, ...dateless];
}

function filterDone(tasks, listId) {
  return tasks.filter(t => t.listId === listId && t.done)
              .sort((a, b) => b.done.localeCompare(a.done));
}

function formatDue(due, today) {
  const dueD = new Date(due);
  const todayD = new Date(today);
  const days = Math.round((dueD - todayD) / 86400000);
  if (days < 0) return { label: dueD.toLocaleDateString(undefined, { month: 'short', day: 'numeric' }), overdue: true };
  if (days === 0) return { label: 'today' };
  if (days === 1) return { label: 'tomorrow' };
  if (days < 7) return { label: dueD.toLocaleDateString(undefined, { weekday: 'long' }).toLowerCase() };
  return { label: dueD.toLocaleDateString(undefined, { month: 'short', day: 'numeric' }) };
}

function renderTask(task, listName, today) {
  const due = task.due ? formatDue(task.due, today) : null;
  return el('div', { class: 'task' + (task.done ? ' done' : '') },
    el('div', { class: 'name' },
      task.name,
      task.done
        ? el('span', { class: 'due' }, task.done)
        : due && el('span', { class: 'due' + (due.overdue ? ' overdue' : '') }, due.label),
    ),
    task.done
      ? el('button', { title: 'Undo', on: { click: () => action('/api/undo', { list: listName, name: task.name }) } }, '↺')
      : el('button', { title: 'Done', on: { click: () => action('/api/done', { list: listName, name: task.name }, `done: ${task.name}`) } }, '✓'),
    !task.done
      ? el('button', { class: 'continue-btn', title: 'Continue', on: { click: () => action('/api/continue', { list: listName, task: task.name }) } }, '»')
      : null,
    el('button', { title: 'Delete', on: { click: () => {
      if (confirm(`Delete "${task.name}"?`)) action('/api/delete', { list: listName, name: task.name });
    } } }, '×'),
  );
}

function renderList(list, allTasks, today, mode) {
  const pending = filterPending(allTasks, list.id, mode, today);
  const done = filterDone(allTasks, list.id);

  const doneSection = el('div', { class: 'done-section' });
  const toggleBtn = el('button', { class: 'done-toggle' });

  const expanded = state.showDone.has(list.id);
  function applyExpanded(open) {
    toggleBtn.textContent = open ? 'hide done' : `show done (${done.length})`;
    doneSection.replaceChildren(...(open ? done.map(t => renderTask(t, list.name, today)) : []));
  }
  applyExpanded(expanded);

  toggleBtn.addEventListener('click', () => {
    const next = !state.showDone.has(list.id);
    next ? state.showDone.add(list.id) : state.showDone.delete(list.id);
    applyExpanded(next);
  });

  const addInput = el('input', { type: 'text', placeholder: 'add task…' });
  const dueInput = el('input', { type: 'date' });
  const submit = () => {
    const name = addInput.value.trim();
    if (!name) return;
    action('/api/add', { list: list.name, name, due: dueInput.value || null });
    addInput.value = '';
    dueInput.value = '';
  };

  return el('div', { class: 'list' },
    el('h3', {}, list.name, el('span', { class: 'count' }, String(pending.length))),
    pending.length
      ? pending.map(t => renderTask(t, list.name, today))
      : el('div', { class: 'empty' }, 'no tasks'),
    el('div', { class: 'add-task' }, addInput, dueInput,
      el('button', { on: { click: submit } }, '+')),
    done.length ? toggleBtn : null,
    doneSection,
  );
}

function renderListsView(mode) {
  if (!state.data) return;
  const { groups, lists, tasks, today } = state.data;
  main.replaceChildren();

  const filterBar = el('div', { class: 'filter-bar' },
    ...['all', 'week', 'today'].map(f => {
      const btn = el('button', { class: f === mode ? 'active' : '' }, f[0].toUpperCase() + f.slice(1));
      btn.addEventListener('click', () => {
        state.taskFilter = f;
        render();
      });
      return btn;
    }),
  );
  main.append(filterBar);

  if (!lists.length) {
    main.append(el('div', { class: 'empty' }, 'no lists yet — add a task to get started'));
    return;
  }

  const seen = new Set();
  for (const g of groups) {
    const groupLists = lists.filter(l => l.groupId === g.id);
    if (!groupLists.length) continue;
    main.append(el('div', { class: 'group-title' }, g.name));
    main.append(el('div', { class: 'lists' },
      groupLists.map(l => renderList(l, tasks, today, mode))));
    groupLists.forEach(l => seen.add(l.id));
  }
  const ungrouped = lists.filter(l => !seen.has(l.id));
  if (ungrouped.length) {
    if (groups.some(g => lists.some(l => l.groupId === g.id))) {
      main.append(el('div', { class: 'group-title' }, 'ungrouped'));
    }
    main.append(el('div', { class: 'lists' },
      ungrouped.map(l => renderList(l, tasks, today, mode))));
  }
}

function renderDaysheet() {
  main.replaceChildren();
  const dateInput = el('input', { type: 'date', value: state.daysheetDate, on: {
    change: e => { state.daysheetDate = e.target.value; refresh(); },
  } });
  main.append(el('div', { class: 'daysheet-controls' },
    el('strong', {}, 'Day Sheet'),
    dateInput,
  ));

  if (!state.daysheet) return;
  const { entries } = state.daysheet;

  if (!entries.length) {
    main.append(el('div', { class: 'empty' }, `No entries for ${state.daysheet.date}`));
  } else {
    const bySect = new Map();
    for (const e of entries) {
      if (!bySect.has(e.sectionId)) bySect.set(e.sectionId, { name: e.sectionName, inGroup: e.inGroup, items: [] });
      bySect.get(e.sectionId).items.push(e);
    }
    for (const { name, inGroup, items } of [...bySect.values()].sort((a, b) => a.name.localeCompare(b.name))) {
      main.append(el('div', { class: 'sheet-list' },
        el('h3', {}, name),
        ...items.map(e => {
          const prefix = inGroup ? `[${e.listName}] ` : '';
          const label = e.type === 'done' ? `Finished ${e.text}`
            : e.type === 'continue' ? `Continued ${e.text}`
            : e.text;
          const deleteBtn = el('button', { class: 'entry-delete', title: 'Delete', on: { click: () => {
            action('/api/daysheet/delete', { id: e.id });
          }}}, '✕');
          return el('div', { class: 'sheet-entry ' + e.type },
            el('span', { class: 'time' }, e.datetime.slice(11, 16)),
            el('span', { class: 'text' }, prefix + label),
            deleteBtn,
          );
        }),
      ));
    }
  }

  const lists = state.data?.lists || [];
  if (!lists.length) return;

  const logList = el('select', {}, lists.map(l => el('option', { value: l.name }, l.name)));
  const logText = el('input', { type: 'text', placeholder: 'log entry…' });
  const logSubmit = () => {
    if (!logText.value.trim()) return;
    action('/api/log', { list: logList.value, text: logText.value.trim() });
    logText.value = '';
  };

  main.append(el('div', { class: 'sheet-form' },
    el('fieldset', {},
      el('legend', {}, 'Log'),
      logList, logText,
      el('button', { on: { click: logSubmit } }, 'Add log'),
    ),
  ));
}

function render() {
  if (state.view === 'daysheet') renderDaysheet();
  else renderListsView(state.taskFilter);
}

document.querySelectorAll('#tabs button').forEach(btn => {
  btn.addEventListener('click', () => {
    document.querySelectorAll('#tabs button').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    state.view = btn.dataset.view;
    refresh();
  });
});

refresh();
