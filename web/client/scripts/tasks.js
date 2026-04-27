'use strict';

// ────────────────────────── Task row ──────────────────────────

function taskRow(task, listName) {
  const due = task.due ? formatDue(task.due) : null;
  let row;

  const checkEl = el('div', {
    class: 'task-check',
    title: task.done ? 'Mark pending' : 'Mark done',
    on: {
      click: () => task.done
        ? act(API.undo, { list: listName, name: task.name })
        : act(API.done, { list: listName, name: task.name }),
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

  const editBtn = el('button', { class: 'task-btn edt', title: 'Rename',
    on: { click: () => {
      const nameIn = el('input', { type: 'text', value: task.name, class: 'task-edit-name', autocomplete: 'off' });
      const dueIn  = el('input', { type: 'date', value: task.due || '', class: 'task-edit-due' });
      const save = async () => {
        const newName = nameIn.value.trim();
        if (!newName) return;
        await act(API.edit, { list: listName, name: task.name, newName, due: dueIn.value || null });
      };
      nameIn.addEventListener('keydown', e => {
        if (e.key === 'Enter') save();
        if (e.key === 'Escape') refresh();
      });
      const saveBtn = el('button', { class: 'task-btn sav', title: 'Save', on: { click: save } }, icon(IC.check, 11));
      const editRow = el('div', { class: 'task-row task-edit-row' },
        el('div', { class: 'task-left' }),
        el('div', { class: 'task-edit-body' }, nameIn, dueIn),
        el('div', { class: 'task-right' }, saveBtn),
      );
      row.replaceWith(editRow);
      nameIn.focus();
      nameIn.select();
    }}
  }, icon(IC.edit, 11));

  const moveBtn = el('button', { class: 'task-btn mov', title: 'Move to list',
    on: { click: () => {
      const allLists = sortByName(state.data.lists);
      const sel = el('select', { class: 'task-move-select' },
        ...allLists.map(l => el('option', { value: l.name, selected: l.name === listName }, l.name)),
      );
      const saveBtn = el('button', { class: 'task-btn sav', title: 'Save',
        on: { click: () => { if (sel.value && sel.value !== listName) act(API.moveTask, { list: listName, name: task.name, newList: sel.value }); else refresh(); } },
      }, icon(IC.check, 11));
      row.replaceWith(el('div', { class: 'task-row task-move-row' },
        sel,
        el('div', { class: 'task-right' }, saveBtn),
      ));
      sel.focus();
    }}
  }, icon(IC.move, 11));

  const deleteBtn = el('button', { class: 'task-btn del', title: 'Delete',
    on: { click: () => { if (confirm(`Delete "${task.name}"?`)) act(API.delete, { list: listName, name: task.name }); } } },
    icon(IC.delete, 11));

  row = el('div', { class: 'task-row' + (task.done ? ' done' : '') },
    el('div', { class: 'task-left' }, checkEl, continueEl),
    el('div', { class: 'task-body' },
      el('span', { class: 'task-name' }, task.name),
      dueEl,
    ),
    el('div', { class: 'task-right' },
      el('div', { class: 'task-edit-actions' }, moveBtn, editBtn),
      deleteBtn,
    ),
  );
  return row;
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
