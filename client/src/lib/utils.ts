import type { MouseEvent } from 'react';
import type { StateResponse, Task, TaskFilter } from './types';

const MS_PER_DAY = 86_400_000;
const OTHERS_RE = /^others?$/i;

const MSG = {
  noTasks: 'No tasks',
  noEntries: 'No entries',
  addTask: 'Add task...',
  entryText: 'Entry text...',
  listName: 'List name...',
  groupName: 'Group name...',
  newList: '+ New List',
  newGroup: '+ New Group',
  today: 'Today',
  yesterday: 'Yesterday',
  tomorrow: 'Tomorrow',
  daysheet: 'Daysheet',
  tasks: 'Tasks',
  others: 'Others',
  calendar: 'Calendar',
} as const;

const localDateStr = (date: Date) => {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
};

const todayStr = () => localDateStr(new Date());

const byName = <T extends { name: string }>(a: T, b: T) =>
  a.name.localeCompare(b.name);

const byDueThenName = (a: Task, b: Task) =>
  (a.due ?? '').localeCompare(b.due ?? '') || byName(a, b);

const sortByName = <T extends { name: string }>(arr: T[]) =>
  [...arr].sort((a, b) => {
    if (OTHERS_RE.test(a.name)) return 1;
    if (OTHERS_RE.test(b.name)) return -1;
    return byName(a, b);
  });

const cx = (...classes: Array<string | false | null | undefined>) =>
  classes.filter(Boolean).join(' ');

const stop = (fn: () => void) => (e: MouseEvent) => {
  e.stopPropagation();
  fn();
};

const flaggedFirst = (tasks: Task[]) => [
  ...tasks.filter(t => t.flagged),
  ...tasks.filter(t => !t.flagged),
];

const pendingFor = (data: StateResponse, listId: string, filter: TaskFilter) => {
  const today = new Date(data.today);
  const pending = data.tasks.filter(t => t.listId === listId && !t.doneAt);

  if (filter === 'day') {
    return flaggedFirst(
      pending.filter(t => t.flagged || (t.due && new Date(t.due) <= today)).sort(byDueThenName),
    );
  }

  if (filter === 'week') {
    const cut = new Date(today);
    cut.setDate(cut.getDate() + 7);

    return flaggedFirst(
      pending.filter(t => t.flagged || (t.due && new Date(t.due) <= cut)).sort(byDueThenName),
    );
  }

  return flaggedFirst([
    ...pending.filter(t => t.due).sort(byDueThenName),
    ...pending.filter(t => !t.due).sort(byName),
  ]);
};

const doneFor = (data: StateResponse, listId: string) =>
  data.tasks
    .filter(t => t.listId === listId && t.doneAt)
    .sort((a, b) => (b.doneAt ?? '').localeCompare(a.doneAt ?? ''));

const weekdayName = (date: Date) =>
  date.toLocaleDateString(undefined, { weekday: 'long' });

const formatDue = (due: string, today: string) => {
  const dueDate = new Date(due);
  const todayDate = new Date(today);
  const days = Math.round((dueDate.getTime() - todayDate.getTime()) / MS_PER_DAY);

  if (days === -1) {
    return {
      label: 'Yesterday',
      cls: 'due-overdue',
    };
  }

  if (days > -7 && days < 0) {
    return {
      label: `Last ${weekdayName(dueDate)}`,
      cls: 'due-overdue',
    };
  }

  if (days < 0) {
    return {
      label: dueDate.toLocaleDateString(undefined, { month: 'short', day: 'numeric' }),
      cls: 'due-overdue',
    };
  }

  if (days === 0) return { label: 'Today', cls: 'due-today' };
  if (days === 1) return { label: 'Tomorrow', cls: 'due-upcoming' };

  if (days < 7) {
    return {
      label: `Next ${weekdayName(dueDate)}`,
      cls: 'due-upcoming',
    };
  }

  return {
    label: dueDate.toLocaleDateString(undefined, { month: 'short', day: 'numeric' }),
    cls: 'due-upcoming',
  };
};

export {
  MSG,
  cx,
  localDateStr,
  todayStr,
  sortByName,
  stop,
  pendingFor,
  doneFor,
  formatDue,
};
