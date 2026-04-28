import { useCallback, useEffect, useState } from 'react';
import type { ReactNode } from 'react';
import {
  Navigate,
  Route,
  Routes,
  useLocation,
  useNavigate,
  useParams,
  useSearchParams,
} from 'react-router-dom';

import styles from './App.module.css';
import { Sidebar } from './components/Sidebar/Sidebar';
import { TaskDetail } from './components/tasks/TaskDetail';
import { Topbar } from './components/Topbar';
import { useAppData } from './hooks/useAppData';
import { useIsMobile } from './hooks/useIsMobile';
import { useIsNarrow } from './hooks/useIsNarrow';
import { api, setUnauthorizedHandler } from './lib/api';
import type { StateResponse, Task, TaskFilter } from './lib/types';
import { cx } from './lib/utils';
import { CalendarView } from './views/CalendarView';
import { CardsView } from './views/CardsView';
import { DaysheetView } from './views/DaysheetView';
import { FocusedView } from './views/FocusedView';
import { LoginView } from './views/LoginView';

type Action = (path: string, body: unknown) => Promise<void>;

type RouteProps = {
  data: StateResponse;
  filter: TaskFilter;
  act: Action;
  openDetail: (task: Task) => void;
};

type RequireDataProps = {
  data: StateResponse | null;
  children: (data: StateResponse) => ReactNode;
};

const RequireData = ({ data, children }: RequireDataProps) => {
  if (!data) return <p>Loading...</p>;
  return children(data);
};

const TasksRoute = ({ data, filter, act, openDetail }: RouteProps) => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();

  return (
    <CardsView
      data={data}
      filter={filter}
      selectedGroup={searchParams.get('group')}
      selectGroup={id => navigate(id ? `/tasks?group=${id}` : '/tasks')}
      selectList={id => navigate(`/list/${id}`)}
      act={act}
      openDetail={openDetail}
    />
  );
};

const ListRoute = ({ data, filter, act, openDetail }: RouteProps) => {
  const { listId } = useParams<{ listId: string }>();

  if (!listId) {
    return <Navigate to="/tasks" replace />;
  }

  return <FocusedView data={data} listId={listId} filter={filter} act={act} openDetail={openDetail} />;
};

type AuthenticatedAppProps = {
  onLogout: () => void;
};

const AuthenticatedApp = ({ onLogout }: AuthenticatedAppProps) => {
  const [filter, setFilter] = useState<TaskFilter>('all');
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [selectedTaskId, setSelectedTaskId] = useState<string | null>(null);
  const { data, calendarUrl, act, refresh, logout } = useAppData();
  const isMobile = useIsMobile();
  const isNarrow = useIsNarrow();

  const handleLogout = useCallback(async () => {
    await logout();
    onLogout();
  }, [logout, onLogout]);

  const selectedTask = selectedTaskId && data
    ? (data.tasks.find(t => t.id === selectedTaskId) ?? null)
    : null;
  const selectedTaskList = selectedTask
    ? (data!.lists.find(l => l.id === selectedTask.listId) ?? null)
    : null;
  const panelOpen = !!(selectedTask && selectedTaskList);

  const openDetail = useCallback((task: Task) => setSelectedTaskId(task.id), []);
  const closeDetail = useCallback(() => setSelectedTaskId(null), []);

  const location = useLocation();
  const { pathname } = location;
  const showingCalendar = pathname === '/calendar' && calendarUrl;
  const activeCalendarUrl = isMobile
    ? calendarUrl.replace('mode=WEEK', 'mode=AGENDA')
    : calendarUrl;

  useEffect(() => {
    if (!isMobile) {
      setSidebarOpen(false);
    }
  }, [isMobile]);

  useEffect(() => {
    setSidebarOpen(false);
    closeDetail();
  }, [location, closeDetail]);

  return (
    <>
      <Sidebar
        data={data}
        filter={filter}
        act={act}
        refresh={refresh}
        isMobile={isMobile}
        isOpen={sidebarOpen}
        onClose={() => setSidebarOpen(false)}
      />
      {isMobile && sidebarOpen && (
        <button
          aria-label="Close navigation"
          className={styles.sidebarBackdrop}
          onClick={() => setSidebarOpen(false)}
        />
      )}
      <div className={styles.content}>

        <Topbar
          filter={filter}
          setFilter={setFilter}
          showMenuButton={isMobile}
          onMenuClick={() => setSidebarOpen(true)}
          onLogout={handleLogout}
        />
        <main className={cx(styles.main, panelOpen && styles.mainWithPanel)}>

          <div
            className={cx(styles.routeContent, isNarrow && panelOpen && styles.routeContentHidden)}
            hidden={false}
          >
            <div hidden={!!showingCalendar}>
              <Routes>
                <Route path="/" element={<Navigate to="/tasks" replace />} />
                <Route path="/calendar" element={<CalendarView calendarUrl={calendarUrl} />} />
                <Route path="/daysheet" element={<DaysheetView data={data} act={act} refresh={refresh} />} />
                <Route
                  path="/tasks"
                  element={
                    <RequireData data={data}>
                      {data => <TasksRoute data={data} filter={filter} act={act} openDetail={openDetail} />}
                    </RequireData>
                  }
                />
                <Route
                  path="/list/:listId"
                  element={
                    <RequireData data={data}>
                      {data => <ListRoute data={data} filter={filter} act={act} openDetail={openDetail} />}
                    </RequireData>
                  }
                />
              </Routes>
            </div>

            {calendarUrl && (
              <iframe
                hidden={!showingCalendar}
                className={styles.calendarFrame}
                src={activeCalendarUrl}
                title="Calendar"
              />
            )}
          </div>

          {panelOpen && (
            <TaskDetail
              task={selectedTask!}
              list={selectedTaskList!}
              today={data!.today}
              act={act}
              onClose={closeDetail}
            />
          )}
        </main>
      </div>
    </>
  );
};

const App = () => {
  const [authenticated, setAuthenticated] = useState<boolean | null>(null);

  useEffect(() => {
    setUnauthorizedHandler(() => setAuthenticated(false));
    api.authStatus().then(res => {
      setAuthenticated(res?.authenticated ?? false);
    });
  }, []);

  if (authenticated === null) return null;
  if (!authenticated) return (
    <Routes>
      <Route path="/login" element={<LoginView />} />
      <Route path="*" element={<Navigate to="/login" replace />} />
    </Routes>
  );
  return <AuthenticatedApp onLogout={() => setAuthenticated(false)} />;
};

export type { Action };
export { App };
