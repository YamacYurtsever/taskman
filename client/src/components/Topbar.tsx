import { useLocation } from 'react-router-dom';
import type { TaskFilter } from '../lib/types';
import { MenuIcon, SignOutIcon } from './icons';
import { ThemeToggle } from './ThemeToggle';
import styles from './Topbar.module.css';

type TopbarProps = {
  filter: TaskFilter;
  setFilter: (filter: TaskFilter) => void;
  showMenuButton: boolean;
  onMenuClick: () => void;
  onLogout?: () => void;
};

const filters: TaskFilter[] = ['all', 'week', 'day'];

const label = (f: TaskFilter) =>
  f[0].toUpperCase() + f.slice(1);

const Topbar = ({ filter, setFilter, showMenuButton, onMenuClick, onLogout }: TopbarProps) => {
  const { pathname } = useLocation();

  const showFilter =
    pathname === '/tasks' || pathname.startsWith('/list/');

  return (
    <div className={styles.topbar}>
      {showMenuButton && (
        <button className={styles.menuBtn} title="Open navigation" onClick={onMenuClick}>
          <MenuIcon size={14} />
        </button>
      )}

      {showFilter && (
        <div className={styles.filterPills}>
          {filters.map(f => (
            <button
              key={f}
              className={
                filter === f
                  ? `${styles.filterPill} ${styles.active}`
                  : styles.filterPill
              }
              onClick={() => setFilter(f)}
            >
              {label(f)}
            </button>
          ))}
        </div>
      )}

      <div className={styles.rightControls}>
        <ThemeToggle />
        {onLogout && (
          <button className={styles.logoutBtn} title="Sign out" onClick={onLogout}>
            <SignOutIcon size={14} />
          </button>
        )}
      </div>
    </div>
  );
};

export { Topbar };
