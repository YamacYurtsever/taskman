import { state, el, icon, MSG, API, IC, sortByName, todayStr, act, refresh } from './core.js';

export function renderDaysheetView() {
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
        el('button', { class: 'date-nav-btn', on: { click: () => shiftDay(-1) } }, icon(IC.chevL)),
        el('span', { class: 'date-nav-label' }, dateLabel(state.daysheetDate)),
        el('button', { class: 'date-nav-btn', on: { click: () => shiftDay(1) } }, icon(IC.chevR)),
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
              icon(IC.delete));

            let entry;
            const editBtn = e.type !== 'log' ? null : el('button', { class: 'task-btn edt timeline-del', title: 'Edit',
              on: { click: () => {
                const editIn = el('input', { type: 'text', value: e.text, class: 'timeline-edit-input', autocomplete: 'off' });
                const save = async () => {
                  const newText = editIn.value.trim();
                  if (!newText) return;
                  await act(API.daysheetEdit, { id: e.id, text: newText });
                };
                editIn.addEventListener('keydown', ev => {
                  if (ev.key === 'Enter') save();
                  if (ev.key === 'Escape') refresh();
                });
                const saveBtn = el('button', { class: 'task-btn sav timeline-del', title: 'Save', on: { click: save } }, icon(IC.check));
                const editRow = el('div', { class: 'timeline-entry timeline-edit-row' },
                  el('span', { class: 'timeline-time' }, e.datetime.slice(11, 16)),
                  editIn,
                  el('div', { class: 'timeline-actions' }, saveBtn),
                );
                entry.replaceWith(editRow);
                editIn.focus();
                editIn.select();
              }}
            }, icon(IC.edit));

            const prefix = e.type === 'done' ? 'Finished ' : e.type === 'continue' ? 'Continued ' : '';
            entry = el('div', { class: 'timeline-entry' },
              el('span', { class: 'timeline-time' }, e.datetime.slice(11, 16)),
              el('span', { class: 'timeline-text' }, prefix + e.text, listTag),
              el('div', { class: 'timeline-actions' }, editBtn, delBtn),
            );
            return entry;
          }),
        ),
      );
    }
  }

  view.append(timeline);

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
        el('button', { class: 'log-form-btn', on: { click: logSubmit } }, icon(IC.plus)),
      ),
    );
  }

  main.append(view);
}
