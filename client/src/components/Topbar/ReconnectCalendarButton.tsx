import { CalendarWarningIcon } from '../icons';
import styles from './ThemeToggle.module.css';

type ReconnectCalendarButtonProps = {
  onClick: () => void;
};

const ReconnectCalendarButton = ({ onClick }: ReconnectCalendarButtonProps) => (
  <button
    className={styles.themeToggle}
    title="Google Calendar access expired — click to reconnect"
    onClick={onClick}
  >
    <CalendarWarningIcon />
  </button>
);

export { ReconnectCalendarButton };
