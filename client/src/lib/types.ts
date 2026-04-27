type TaskFilter = 'all' | 'week' | 'day';

type Group = {
  id: string;
  name: string;
};

type TaskList = {
  id: string;
  name: string;
  groupId: string | null;
};

type Task = {
  id: string;
  name: string;
  listId: string;
  due: string | null;
  done: string | null;
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
};

type DaysheetEntry = {
  id: string;
  datetime: string;
  listId: string;
  type: 'log' | 'continue' | 'done';
  text: string;
  listName: string;
  sectionId: string;
  sectionName: string;
  inGroup: boolean;
};

type DaysheetResponse = {
  date: string;
  entries: DaysheetEntry[];
};

type ApiResult = {
  ok: boolean;
  message: string;
};

export type {
  TaskFilter,
  Group,
  TaskList,
  Task,
  StateResponse,
  ConfigResponse,
  DaysheetEntry,
  DaysheetResponse,
  ApiResult,
};
