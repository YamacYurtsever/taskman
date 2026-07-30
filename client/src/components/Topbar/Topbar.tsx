import { useLocation } from 'react-router-dom';
import type { CSSProperties } from 'react';
import type { TaskFilter } from '../../lib/types';
import { AccentPicker } from './AccentPicker';
import { InfoButton } from './InfoButton';
import { MenuIcon, SignOutIcon } from '../icons';
import { NextEventPill } from './NextEventPill';
import { SettingsMenu } from './SettingsMenu';
import { SoundToggle } from './SoundToggle';
import { ThemeToggle } from './ThemeToggle';
import styles from './Topbar.module.css';

type TopbarProps = {
  filter: TaskFilter;
  setFilter: (filter: TaskFilter) => void;
  showMenuButton: boolean;
  onMenuClick: () => void;
  onLogout?: () => void;
  accentColor?: string | null;
  onAccentColorChange?: (color: string | null) => void;
  onInfoClick?: () => void;
  onOpenDayCalendar?: (date: string) => void;
};

const filters: TaskFilter[] = ['all', 'week', 'day'];

const label = (f: TaskFilter) =>
  f[0].toUpperCase() + f.slice(1);

const Topbar = ({
  filter,
  setFilter,
  showMenuButton,
  onMenuClick,
  onLogout,
  accentColor,
  onAccentColorChange,
  onInfoClick,
  onOpenDayCalendar,
}: TopbarProps) => {
  const { pathname } = useLocation();
  const activeIndex = filters.indexOf(filter);

  const showFilter =
    pathname === '/tasks' || pathname.startsWith('/list/');

  return (
    <div className={styles.topbar}>
      <div className={styles.leftControls}>
        {showMenuButton && (
          <button className={styles.menuBtn} title="Open navigation" onClick={onMenuClick}>
            <MenuIcon size={14} />
          </button>
        )}
        <NextEventPill onOpenDay={onOpenDayCalendar} />
      </div>

      {showFilter && (
        <div
          className={styles.filterPills}
          style={{ '--active-index': activeIndex } as CSSProperties}
        >
          <div className={styles.filterIndicator} aria-hidden="true" />
          {filters.map(f => (
            <button
              key={f}
              className={styles.filterPill}
              aria-pressed={filter === f}
              onClick={() => setFilter(f)}
            >
              {label(f)}
            </button>
          ))}
        </div>
      )}

      <SettingsMenu>
        {onInfoClick && <InfoButton onClick={onInfoClick} />}
        <SoundToggle />
        <ThemeToggle />
        {onAccentColorChange && (
          <AccentPicker accentColor={accentColor ?? null} onChange={onAccentColorChange} />
        )}
        {onLogout && (
          <button className={styles.logoutBtn} title="Sign out" onClick={onLogout}>
            <SignOutIcon />
          </button>
        )}
      </SettingsMenu>
    </div>
  );
};

export { Topbar };
