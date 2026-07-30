import { useCallback, useEffect, useRef, useState } from 'react';
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
import { DayCalendarPanelBody, DayCalendarPanelHeader } from './components/Panel/DayCalendarPanel';
import { InfoPanelBody, InfoPanelHeader } from './components/Panel/InfoPanel';
import { Panel } from './components/Panel/Panel';
import type { PanelSize } from './components/Panel/Panel';
import { TaskPanelBody, TaskPanelHeader } from './components/Panel/TaskPanel';
import { Sidebar } from './components/Sidebar/Sidebar';
import { Topbar } from './components/Topbar/Topbar';
import { useAppData } from './hooks/useAppData';
import { useIsMobile } from './hooks/useIsMobile';
import { useIsNarrow } from './hooks/useIsNarrow';
import { api, setUnauthorizedHandler } from './lib/api';
import type { StateResponse, Task, TaskFilter } from './lib/types';
import { cx, MSG } from './lib/utils';
import { CalendarView } from './views/CalendarView';
import { CardsView } from './views/CardsView';
import { DaysheetView } from './views/DaysheetView';
import { FocusedView } from './views/FocusedView';
import { LoginView } from './views/LoginView';

type Action = (path: string, body: unknown) => Promise<boolean>;

const PANEL_SIZE_KEY = 'panelSize';
// Matches --animation-d-lg, the duration of Panel's slide-out CSS animation.
const PANEL_EXIT_MS = 320;

const loadStoredPanelSize = (): PanelSize => {
  const raw = localStorage.getItem(PANEL_SIZE_KEY);
  if (!raw) return null;
  if (raw === 'full') return 'full';
  const n = Number(raw);
  return Number.isFinite(n) ? n : null;
};

type SidePanel =
  | { type: 'task'; taskId: string }
  | { type: 'info' }
  | { type: 'day-calendar'; date: string }
  | null;

type RouteProps = {
  data: StateResponse;
  filter: TaskFilter;
  act: Action;
  openDetail: (task: Task) => void;
};

type RequireDataProps = {
  loading: boolean;
  data: StateResponse | null;
  children: (data: StateResponse) => ReactNode;
};

const RequireData = ({ loading, data, children }: RequireDataProps) => {
  if (loading) return <p>Loading...</p>;
  if (!data) return <div className="empty">{MSG.noTasks}</div>;
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
  const [sidePanel, setSidePanel] = useState<SidePanel>(null);
  const [lastSidePanel, setLastSidePanel] = useState<SidePanel>(null);
  const [panelMounted, setPanelMounted] = useState(false);
  const [panelClosing, setPanelClosing] = useState(false);
  const [panelSize, setPanelSize] = useState<PanelSize>(loadStoredPanelSize);
  const panelCloseTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const wasPanelOpenRef = useRef(false);
  const {
    data,
    calendarUrl,
    accentColor,
    setAccentColor,
    loading,
    act,
    refresh,
    logout,
    reconnectCalendar,
  } = useAppData();
  const isMobile = useIsMobile();
  const isNarrow = useIsNarrow();

  const handlePanelResize = useCallback((size: PanelSize) => {
    setPanelSize(size);
    if (size === null) {
      localStorage.removeItem(PANEL_SIZE_KEY);
    } else {
      localStorage.setItem(PANEL_SIZE_KEY, String(size));
    }
  }, []);

  useEffect(() => {
    if (isNarrow) handlePanelResize(null);
  }, [isNarrow, handlePanelResize]);

  const handleLogout = useCallback(async () => {
    await logout();
    onLogout();
  }, [logout, onLogout]);

  const currentTask = sidePanel?.type === 'task' && data
    ? (data.tasks.find(t => t.id === sidePanel.taskId) ?? null)
    : null;
  const currentTaskList = currentTask
    ? (data!.lists.find(l => l.id === currentTask.listId) ?? null)
    : null;
  const showingInfoNow = sidePanel?.type === 'info';
  const showingDayCalendarNow = sidePanel?.type === 'day-calendar';
  // Whether the panel should be open right now — driven straight off sidePanel,
  // used only to decide the animation direction (see the effect below).
  const targetOpen = showingInfoNow || showingDayCalendarNow || !!(currentTask && currentTaskList);

  // The panel keeps rendering its last content while it fades out, since sidePanel
  // itself goes back to null immediately on close (before the exit animation ends).
  useEffect(() => {
    if (targetOpen) setLastSidePanel(sidePanel);
  }, [targetOpen, sidePanel]);

  useEffect(() => {
    const wasOpen = wasPanelOpenRef.current;
    wasPanelOpenRef.current = targetOpen;

    if (targetOpen) {
      if (panelCloseTimerRef.current) clearTimeout(panelCloseTimerRef.current);
      setPanelClosing(false);
      setPanelMounted(true);
      return;
    }

    if (wasOpen) {
      setPanelClosing(true);
      panelCloseTimerRef.current = setTimeout(() => {
        setPanelMounted(false);
        setPanelClosing(false);
      }, PANEL_EXIT_MS);
    }
  }, [targetOpen]);

  useEffect(() => {
    return () => {
      if (panelCloseTimerRef.current) clearTimeout(panelCloseTimerRef.current);
    };
  }, []);

  const displayedTask = lastSidePanel?.type === 'task' && data
    ? (data.tasks.find(t => t.id === lastSidePanel.taskId) ?? null)
    : null;
  const displayedTaskList = displayedTask
    ? (data!.lists.find(l => l.id === displayedTask.listId) ?? null)
    : null;
  const showingInfo = lastSidePanel?.type === 'info';
  const displayedDayCalendarDate = lastSidePanel?.type === 'day-calendar' ? lastSidePanel.date : null;
  const showingDayCalendar = !!displayedDayCalendarDate;

  const openDetail = useCallback((task: Task) => setSidePanel({ type: 'task', taskId: task.id }), []);
  const openInfo = useCallback(() => setSidePanel({ type: 'info' }), []);
  const openDayCalendar = useCallback((date: string) => setSidePanel({ type: 'day-calendar', date }), []);
  const closeDetail = useCallback(() => setSidePanel(null), []);

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
          accentColor={accentColor}
          onAccentColorChange={setAccentColor}
          onInfoClick={openInfo}
          onOpenDayCalendar={openDayCalendar}
        />
        <main className={cx(styles.main, panelMounted && styles.mainWithPanel)}>

          <div
            className={cx(
              styles.routeContent,
              panelMounted && (isNarrow || panelSize === 'full') && styles.routeContentHidden,
            )}
            hidden={false}
          >
            <div className={styles.routeInner} hidden={!!showingCalendar}>
              <Routes>
                <Route path="/" element={<Navigate to="/tasks" replace />} />
                <Route
                  path="/calendar"
                  element={<CalendarView calendarUrl={calendarUrl} onConnect={reconnectCalendar} />}
                />
                <Route path="/daysheet" element={<DaysheetView data={data} act={act} refresh={refresh} />} />
                <Route
                  path="/tasks"
                  element={
                    <RequireData loading={loading} data={data}>
                      {data => <TasksRoute data={data} filter={filter} act={act} openDetail={openDetail} />}
                    </RequireData>
                  }
                />
                <Route
                  path="/list/:listId"
                  element={
                    <RequireData loading={loading} data={data}>
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

          {panelMounted && (
            <Panel
              closing={panelClosing}
              onClose={closeDetail}
              panelSize={panelSize}
              onResize={handlePanelResize}
              resizable={!isNarrow}
              header={
                showingInfo
                  ? <InfoPanelHeader />
                  : showingDayCalendar
                    ? <DayCalendarPanelHeader date={displayedDayCalendarDate!} />
                    : (displayedTask && displayedTaskList && (
                        <TaskPanelHeader task={displayedTask} list={displayedTaskList} today={data!.today} />
                      ))
              }
            >
              {showingInfo
                ? <InfoPanelBody />
                : showingDayCalendar
                  ? <DayCalendarPanelBody calendarUrl={calendarUrl} date={displayedDayCalendarDate!} />
                  : (displayedTask && <TaskPanelBody task={displayedTask} act={act} />)}
            </Panel>
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
