type TaskFilter = 'all' | 'week' | 'day';

type Group = {
  id: string;
  name: string;
};

type TaskList = {
  id: string;
  name: string;
  groupId: string | null;
  pinned?: boolean;
};

type Task = {
  id: string;
  name: string;
  listId: string;
  due: string | null;
  doneAt: string | null;
  description: string;
};

type StateResponse = {
  groups: Group[];
  lists: TaskList[];
  tasks: Task[];
  today: string;
};

type ConfigResponse = {
  calendarUrl: string;
  calendarTimezone: string;
};

type DaysheetEntry = {
  id: string;
  datetime: string;
  localTime: string;
  listId: string;
  type: 'log' | 'continue' | 'done';
  text: string;
  listName: string;
  sectionId: string;
  sectionName: string;
  inGroup: boolean;
};

type PinnedSection = {
  sectionId: string;
  sectionName: string;
  inGroup: boolean;
};

type DaysheetResponse = {
  date: string;
  entries: DaysheetEntry[];
  pinnedSections: PinnedSection[];
};

type ApiResult = {
  ok: boolean;
  message: string;
};

type AuthStatusResponse = {
  authenticated: boolean;
};

export type {
  TaskFilter,
  Group,
  TaskList,
  Task,
  StateResponse,
  ConfigResponse,
  DaysheetEntry,
  PinnedSection,
  DaysheetResponse,
  ApiResult,
  AuthStatusResponse,
};
