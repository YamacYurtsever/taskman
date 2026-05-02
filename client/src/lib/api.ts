import type {
  ApiResult,
  AuthStatusResponse,
  ConfigResponse,
  DaysheetResponse,
  StateResponse,
} from './types';

const API = {
  authStatus: '/api/auth/status',
  oauthStart: '/api/oauth/start',
  logout: '/api/logout',

  config: '/api/config',
  configTimezone: '/api/config/timezone',
  state: '/api/state',
  daysheet: '/api/daysheet',

  add: '/api/add',
  addList: '/api/add-list',
  addGroup: '/api/add-group',
  duplicate: '/api/duplicate',
  moveTask: '/api/move-task',
  moveList: '/api/move-list',
  renameList: '/api/rename-list',
  deleteList: '/api/delete-list',
  renameGroup: '/api/rename-group',
  deleteGroup: '/api/delete-group',

  done: '/api/done',
  undo: '/api/undo',
  delete: '/api/delete',
  continue: '/api/continue',
  edit: '/api/edit',
  log: '/api/log',

  daysheetDelete: '/api/daysheet/delete',
  daysheetEdit: '/api/daysheet/edit',
  taskDescription: '/api/task-description',
  pinList: '/api/pin-list',
} as const;

let unauthorizedHandler: (() => void) | null = null;

const setUnauthorizedHandler = (handler: () => void) => {
  unauthorizedHandler = handler;
};

const request = async <T>(
  method: string,
  path: string,
  body?: unknown,
): Promise<T | null> => {
  const opts: RequestInit = { method };

  if (body !== undefined) {
    opts.headers = { 'Content-Type': 'application/json' };
    opts.body = JSON.stringify(body);
  }

  try {
    const res = await fetch(path, opts);
    const json = await res.json().catch(() => null);

    if (res.status === 401) {
      unauthorizedHandler?.();
      return null;
    }

    if (!res.ok) {
      console.log(json?.message || json?.error || 'Request failed');
      return null;
    }

    return json as T;
  } catch {
    console.log('Request failed');
    return null;
  }
};

const api = {
  authStatus: () => request<AuthStatusResponse>('GET', API.authStatus),
  oauthStart: () => request<{ url: string }>('GET', API.oauthStart),
  logout: () => request<ApiResult>('POST', API.logout),

  config: () => request<ConfigResponse>('GET', API.config),
  setTimezone: (timezone: string) => request<ApiResult>('POST', API.configTimezone, { timezone }),
  state: () => request<StateResponse>('GET', API.state),
  daysheet: (date: string) =>
    request<DaysheetResponse>('GET', `${API.daysheet}?date=${encodeURIComponent(date)}`),
  post: (path: string, body: unknown) => request<ApiResult>('POST', path, body),
};

export {
  API,
  request,
  api,
  setUnauthorizedHandler,
};
