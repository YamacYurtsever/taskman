import { useState } from 'react';
import type { ReactNode } from 'react';
import { API } from '../lib/api';
import { CheckIcon, ChevronLeftIcon, ChevronRightIcon, ContinueIcon, DeleteIcon, EditIcon, MoveIcon, PlusIcon } from '../components/icons';
import type { StateResponse, Task, TaskFilter, TaskList } from '../lib/types';
import { doneFor, formatDue, MSG, pendingFor, sortByName } from '../lib/utils';
import styles from './TasksView.module.css';

type Action = (path: string, body: unknown) => Promise<void>;

type TaskRowProps = {
  data: StateResponse;
  task: Task;
  listName: string;
  act: Action;
  refresh: () => Promise<void>;
};

function TaskRow({ data, task, listName, act, refresh }: TaskRowProps) {
  const [mode, setMode] = useState<'view' | 'edit' | 'move'>('view');
  const [name, setName] = useState(task.name);
  const [due, setDue] = useState(task.due || '');
  const [newList, setNewList] = useState(listName);
  const dueInfo = task.due ? formatDue(task.due, data.today) : null;

  const saveEdit = async () => {
    const newName = name.trim();
    if (!newName) return;
    await act(API.edit, { list: listName, name: task.name, newName, due: due || null });
    setMode('view');
  };

  if (mode === 'edit') {
    return (
      <div className={`${styles.taskRow} ${styles.taskEditRow}`}>
        <div className={styles.taskLeft} />
        <div className={styles.taskEditBody}>
          <input className={styles.taskEditName} autoComplete="off" value={name} autoFocus onChange={e => setName(e.target.value)} onKeyDown={e => {
            if (e.key === 'Enter') saveEdit();
            if (e.key === 'Escape') setMode('view');
          }} />
          <input className={styles.taskEditDue} type="date" value={due} onChange={e => setDue(e.target.value)} />
        </div>
        <div className={styles.taskRight}>
          <button className="task-btn sav" title="Save" onClick={saveEdit}><CheckIcon /></button>
        </div>
      </div>
    );
  }

  if (mode === 'move') {
    return (
      <div className={`${styles.taskRow} ${styles.taskMoveRow}`}>
        <select className={styles.taskMoveSelect} value={newList} autoFocus onChange={e => setNewList(e.target.value)}>
          {sortByName(data.lists).map(l => <option key={l.id} value={l.name}>{l.name}</option>)}
        </select>
        <div className={styles.taskRight}>
          <button className="task-btn sav" title="Save" onClick={async () => {
            if (newList && newList !== listName) await act(API.moveTask, { list: listName, name: task.name, newList });
            setMode('view');
          }}><CheckIcon /></button>
        </div>
      </div>
    );
  }

  return (
    <div className={[styles.taskRow, task.done ? styles.done : ''].filter(Boolean).join(' ')}>
      <div className={styles.taskLeft}>
        <div
          className={styles.taskCheck}
          title={task.done ? 'Mark pending' : 'Mark done'}
          onClick={() => task.done ? act(API.undo, { list: listName, name: task.name }) : act(API.done, { list: listName, name: task.name })}
        >
          <svg className={styles.taskCheckSvg} width="9" height="9" viewBox="0 0 16 16" fill="none" stroke="#fff" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
            <path d="M3 8.5l3 3L13 5" />
          </svg>
        </div>
        {!task.done && (
          <button className="task-btn cnt" title="Log continue" onClick={() => act(API.continue, { list: listName, task: task.name })}>
            <ContinueIcon />
          </button>
        )}
      </div>
      <div className={styles.taskBody}>
        <span className={styles.taskName}>{task.name}</span>
        {dueInfo && <span className={[styles.taskDue, dueInfo.cls ? styles[dueInfo.cls] : ''].filter(Boolean).join(' ')}>{dueInfo.label}</span>}
      </div>
      <div className={styles.taskRight}>
        <div className={styles.taskEditActions}>
          <button className="task-btn mov" title="Move to list" onClick={() => setMode('move')}><MoveIcon /></button>
          <button className="task-btn edt" title="Rename" onClick={() => setMode('edit')}><EditIcon /></button>
        </div>
        <button className="task-btn del" title="Delete" onClick={() => {
          if (confirm(`Delete "${task.name}"?`)) act(API.delete, { list: listName, name: task.name });
        }}><DeleteIcon /></button>
      </div>
    </div>
  );
}

const CARD_LIMIT = 10;

function Card({ data, list, filter, expanded, toggleExpanded, act, refresh, openList }: {
  data: StateResponse;
  list: TaskList;
  filter: TaskFilter;
  expanded: boolean;
  toggleExpanded: () => void;
  act: Action;
  refresh: () => Promise<void>;
  openList: () => void;
}) {
  const pending = pendingFor(data, list.id, filter);
  if (!pending.length) return null;

  const overflow = pending.length > CARD_LIMIT;
  const visible = overflow && !expanded ? pending.slice(0, CARD_LIMIT) : pending;

  return (
    <div className={styles.card}>
      <div className={styles.cardHeader} onClick={openList}>
        <span className={styles.cardTitle}>{list.name}</span>
        <span className={styles.cardCount}>{pending.length}</span>
      </div>
      <div className={styles.cardBody}>
        {visible.map(t => <TaskRow key={t.id} data={data} task={t} listName={list.name} act={act} refresh={refresh} />)}
      </div>
      {overflow && (
        <button className={styles.cardOverflowToggle} onClick={toggleExpanded}>
          {expanded ? <ChevronLeftIcon /> : <ChevronRightIcon />}
          {expanded ? ` hide ${pending.length - CARD_LIMIT}` : ` ${pending.length - CARD_LIMIT} more`}
        </button>
      )}
    </div>
  );
}

export function CardsView({ data, filter, selectedGroup, selectGroup, selectList, act, refresh }: {
  data: StateResponse;
  filter: TaskFilter;
  selectedGroup: string | null;
  selectGroup: (id: string | null) => void;
  selectList: (id: string | null) => void;
  act: Action;
  refresh: () => Promise<void>;
}) {
  const [expandedCards, setExpandedCards] = useState(new Set<string>());

  const toggleExpanded = (id: string) => {
    const next = new Set(expandedCards);
    next.has(id) ? next.delete(id) : next.add(id);
    setExpandedCards(next);
  };

  const renderCards = (lists: TaskList[]) => lists
    .filter(list => pendingFor(data, list.id, filter).length > 0)
    .map(list => (
      <Card
        key={list.id}
        data={data}
        list={list}
        filter={filter}
        expanded={expandedCards.has(list.id)}
        toggleExpanded={() => toggleExpanded(list.id)}
        openList={() => selectList(list.id)}
        act={act}
        refresh={refresh}
      />
    ));

  if (selectedGroup) {
    const group = data.groups.find(g => g.id === selectedGroup);
    if (!group) return null;
    const cards = renderCards(sortByName(data.lists.filter(l => l.groupId === group.id)));
    return (
      <>
        <div className={styles.sectionLabel}>{group.name}</div>
        {cards.length ? <div className={styles.cardsGrid}>{cards}</div> : <div className="empty">{MSG.noTasks}</div>}
      </>
    );
  }

  const sections: ReactNode[] = [];
  const seen = new Set<string>();
  for (const group of sortByName(data.groups)) {
    const lists = sortByName(data.lists.filter(l => l.groupId === group.id));
    const cards = renderCards(lists);
    if (cards.length) {
      sections.push(
        <div key={`${group.id}-label`} className={`${styles.sectionLabel} ${styles.sectionLabelLink}`} onClick={() => selectGroup(group.id)}>
          {group.name}
        </div>
      );
      sections.push(<div key={group.id} className={styles.cardsGrid}>{cards}</div>);
    }
    lists.forEach(l => seen.add(l.id));
  }

  const ungrouped = sortByName(data.lists.filter(l => !seen.has(l.id)));
  const ungroupedCards = renderCards(ungrouped);
  if (ungroupedCards.length) {
    const hasGroups = data.groups.some(g => data.lists.some(l => l.groupId === g.id));
    if (hasGroups) sections.push(<div key="others-label" className={styles.sectionLabel}>{MSG.others}</div>);
    sections.push(<div key="others" className={styles.cardsGrid}>{ungroupedCards}</div>);
  }

  return <>{sections.length ? sections : <div className="empty">{MSG.noTasks}</div>}</>;
}

function AddTaskForm({ listName, act }: { listName: string; act: Action }) {
  const [name, setName] = useState('');
  const [due, setDue] = useState('');

  const submit = async () => {
    const trimmed = name.trim();
    if (!trimmed) return;
    await act(API.add, { list: listName, name: trimmed, due: due || null });
    setName('');
    setDue('');
  };

  return (
    <div className={styles.inlineAdd}>
      <input type="text" placeholder={MSG.addTask} value={name} onChange={e => setName(e.target.value)} onKeyDown={e => e.key === 'Enter' && submit()} />
      <input type="date" value={due} onChange={e => setDue(e.target.value)} />
      <button className={styles.inlineAddBtn} onClick={submit}><PlusIcon /></button>
    </div>
  );
}

export function FocusedView({ data, listId, filter, act, refresh }: {
  data: StateResponse;
  listId: string;
  filter: TaskFilter;
  act: Action;
  refresh: () => Promise<void>;
}) {
  const [showDone, setShowDone] = useState(false);

  const list = data.lists.find(l => l.id === listId);
  if (!list) return <div className="empty">{MSG.noTasks}</div>;

  const pending = pendingFor(data, listId, filter);
  const done = doneFor(data, listId);
  const toggleDone = () => setShowDone(v => !v);

  return (
    <div className={styles.focusedView}>
      <div className={styles.focusedHeader}>
        <h1 className={styles.focusedTitle}>{list.name}</h1>
        <span className={styles.focusedMeta}>{pending.length}</span>
      </div>
      <div className={styles.focusedTasks}>
        {pending.length
          ? pending.map(t => <TaskRow key={t.id} data={data} task={t} listName={list.name} act={act} refresh={refresh} />)
          : <div className="empty">{MSG.noTasks}</div>}
      </div>
      <AddTaskForm listName={list.name} act={act} />
      {done.length > 0 && (
        <div className={styles.doneWrapper}>
          <button className={styles.doneToggle} onClick={toggleDone}>
            {showDone ? <ChevronLeftIcon /> : <ChevronRightIcon />}
            {` ${showDone ? 'hide' : 'show'} done (${done.length})`}
          </button>
          <div className={styles.doneSection}>
            {showDone && done.map(t => <TaskRow key={t.id} data={data} task={t} listName={list.name} act={act} refresh={refresh} />)}
          </div>
        </div>
      )}
    </div>
  );
}
