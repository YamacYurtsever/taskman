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
  flagged: boolean;
  recurIntervalDays: number | null;
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
  accentColor: string | null;
  calendarAuthValid: boolean;
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

type NextEvent = {
  title: string;
  startIso: string;
  endIso: string;
  startTime: string;
  endTime: string;
  hasOverlap: boolean;
  date: string;
};

type NextEventResponse = {
  event: NextEvent | null;
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
  NextEvent,
  NextEventResponse,
};
