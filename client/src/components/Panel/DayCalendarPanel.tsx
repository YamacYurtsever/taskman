import styles from './DayCalendarPanel.module.css';

type DayCalendarPanelHeaderProps = {
  date: string;
};

const formatHeaderDate = (date: string) => {
  const [year, month, day] = date.split('-').map(Number);
  return new Date(year, month - 1, day).toLocaleDateString(undefined, {
    weekday: 'long',
    month: 'long',
    day: 'numeric',
  });
};

const DayCalendarPanelHeader = ({ date }: DayCalendarPanelHeaderProps) => (
  <h2 className={styles.title}>{formatHeaderDate(date)}</h2>
);

type DayCalendarPanelBodyProps = {
  calendarUrl: string;
  date: string;
};

// Google's embed API has no true single-day mode (only AGENDA/WEEK/MONTH) —
// AGENDA scoped to a one-day `dates` range is the closest match, and AGENDA
// is already the mode this app swaps to for the mobile calendar view.
const buildDayUrl = (calendarUrl: string, date: string) => {
  const compact = date.replace(/-/g, '');
  return `${calendarUrl.replace('mode=WEEK', 'mode=AGENDA')}&dates=${compact}/${compact}`;
};

const DayCalendarPanelBody = ({ calendarUrl, date }: DayCalendarPanelBodyProps) => {
  if (!calendarUrl) return <div className="empty">No calendar connected</div>;

  return (
    <div className={styles.frameWrap}>
      <iframe className={styles.frame} src={buildDayUrl(calendarUrl, date)} title="Day calendar" />
    </div>
  );
};

export { DayCalendarPanelHeader, DayCalendarPanelBody };
