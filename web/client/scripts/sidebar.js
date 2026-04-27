'use strict';

function renderSidebar() {
  const nav = document.getElementById('list-nav');
  nav.replaceChildren();
  if (!state.data) return;
  const { groups, lists } = state.data;

  function listBtn(list) {
    const count = pendingFor(list.id).length;
    const active = state.view === 'tasks' && state.selectedList === list.id;
    let item;

    const deleteBtn = el('button', { class: 'lni-action lni-del', title: 'Delete',
      on: { click: e => {
        e.stopPropagation();
        if (confirm(`Delete list "${list.name}" and all its tasks?`)) act(API.deleteList, { list: list.name });
      }}
    }, icon(IC.delete, 10));

    const renameBtn = el('button', { class: 'lni-action edt', title: 'Rename',
      on: { click: e => {
        e.stopPropagation();
        const input = el('input', { type: 'text', value: list.name, autocomplete: 'off' });
        const save = async () => {
          const newName = input.value.trim();
          if (!newName || newName === list.name) { refresh(); return; }
          await act(API.renameList, { list: list.name, newName });
        };
        input.addEventListener('keydown', ev => {
          if (ev.key === 'Enter') save();
          if (ev.key === 'Escape') refresh();
        });
        const saveBtn = el('button', { class: 'lni-action sav', title: 'Save', on: { click: save } }, icon(IC.check, 10));
        item.replaceWith(el('div', { class: 'list-nav-item nav-list lni-rename-row' },
          input,
          el('div', { class: 'lni-right' }, el('div', { class: 'lni-actions' }, saveBtn)),
        ));
        input.focus(); input.select();
      }}
    }, icon(IC.edit, 10));

    const moveGroupBtn = groups.length === 0 ? null : el('button', { class: 'lni-action mov', title: 'Move to group',
      on: { click: e => {
        e.stopPropagation();
        const currentGroup = groups.find(g => g.id === list.groupId);
        const sel = el('select', { class: 'lni-move-select' },
          el('option', { value: '' }, 'No group'),
          ...sortByName(groups).map(g => el('option', { value: g.name }, g.name)),
        );
        sel.value = currentGroup?.name || '';
        const saveBtn = el('button', { class: 'lni-action sav', title: 'Save', on: { click: () => act(API.moveList, { list: list.name, group: sel.value }) } }, icon(IC.check, 10));
        item.replaceWith(el('div', { class: 'list-nav-item nav-list lni-move-row' },
          sel,
          el('div', { class: 'lni-right' }, el('div', { class: 'lni-actions' }, saveBtn)),
        ));
        sel.focus();
      }}
    }, icon(IC.move, 10));

    item = el('button', {
      class: 'list-nav-item nav-list' + (active ? ' active' : ''),
      on: { click: () => { state.selectedList = list.id; state.selectedGroup = null; state.view = 'tasks'; render(); renderSidebar(); } },
    }, list.name,
      el('div', { class: 'lni-right' },
        el('div', { class: 'lni-actions' }, moveGroupBtn, renameBtn, deleteBtn),
        count ? el('span', { class: 'lni-count' }, count) : null,
      ),
    );
    return item;
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
    let groupHeader;

    const grpDeleteBtn = el('button', { class: 'lni-action lni-del', title: 'Delete group',
      on: { click: e => {
        e.stopPropagation();
        if (confirm(`Delete group "${g.name}"? Lists will be ungrouped.`)) act(API.deleteGroup, { group: g.name });
      }}
    }, icon(IC.delete, 10));

    const grpRenameBtn = el('button', { class: 'lni-action edt', title: 'Rename',
      on: { click: e => {
        e.stopPropagation();
        const input = el('input', { type: 'text', value: g.name, autocomplete: 'off' });
        const save = async () => {
          const newName = input.value.trim();
          if (!newName || newName === g.name) { refresh(); return; }
          await act(API.renameGroup, { group: g.name, newName });
        };
        input.addEventListener('keydown', ev => {
          if (ev.key === 'Enter') save();
          if (ev.key === 'Escape') refresh();
        });
        const saveBtn = el('button', { class: 'lni-action sav', title: 'Save', on: { click: save } }, icon(IC.check, 10));
        groupHeader.replaceWith(el('div', { class: 'list-nav-item nav-group-header lni-rename-row' },
          input,
          el('div', { class: 'lni-right' }, el('div', { class: 'lni-actions' }, saveBtn)),
        ));
        input.focus(); input.select();
      }}
    }, icon(IC.edit, 10));

    groupHeader = el('button', {
      class: 'list-nav-item nav-group-header' + (grpActive ? ' active' : ''),
      on: { click: () => { state.selectedGroup = g.id; state.selectedList = null; state.view = 'tasks'; render(); renderSidebar(); } },
    }, g.name, el('div', { class: 'lni-right' }, el('div', { class: 'lni-actions' }, grpRenameBtn, grpDeleteBtn)));
    const groupLists = el('div', { class: 'nav-group-lists' }, ...gl.map(listBtn));
    tasksSectionBody.append(el('div', { class: 'nav-group' }, groupHeader, groupLists));
    gl.forEach(l => seen.add(l.id));
  }

  const ungrouped = sortByName(lists.filter(l => !seen.has(l.id)));
  ungrouped.forEach(l => tasksSectionBody.append(listBtn(l)));

  // New List button — replaces itself with an inline input row on click
  let newListBtn;
  newListBtn = el('button', {
    class: 'new-list-btn',
    on: { click: () => {
      const input = el('input', { type: 'text', placeholder: MSG.listName, autocomplete: 'off' });
      const saveBtn = el('button', { class: 'lni-action sav', title: 'Add',
        on: { click: async () => {
          const name = input.value.trim();
          if (name) await act(API.addList, { list: name });
          else renderSidebar();
        }},
      }, icon(IC.check, 10));
      const inputRow = el('div', { class: 'new-list-input lni-rename-row list-nav-item' }, input,
        el('div', { class: 'lni-right' }, el('div', { class: 'lni-actions' }, saveBtn)),
      );
      input.addEventListener('keydown', e => {
        if (e.key === 'Enter') saveBtn.click();
        if (e.key === 'Escape') renderSidebar();
      });
      newListBtn.replaceWith(inputRow);
      input.focus();
    }},
  }, MSG.newList);
  tasksSectionBody.append(newListBtn);

  nav.append(el('div', { class: 'nav-section' }, tasksHeader, tasksSectionBody));
}
