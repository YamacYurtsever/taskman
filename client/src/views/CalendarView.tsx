import { CalendarIcon } from '../components/icons';
import styles from './CalendarView.module.css';

type CalendarViewProps = {
  calendarUrl: string;
  onConnect: () => void;
};

export function CalendarView({ calendarUrl, onConnect }: CalendarViewProps) {
  if (calendarUrl) return null;

  return (
    <div className={styles.wrap}>
      <button className={styles.connectBtn} onClick={onConnect}>
        <CalendarIcon size={16} />
        Connect Calendar
      </button>
    </div>
  );
}
