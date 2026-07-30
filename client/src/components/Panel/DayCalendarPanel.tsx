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

// Google's embed API has no true single-day mode (only AGENDA/WEEK/MONTH), and
// combining AGENDA with a `dates` range renders a blank iframe rather than an
// error. Keeping the existing (already-working) mode=WEEK URL and just adding
// a `dates` range to jump it to the event's day is the reliable option, even
// though it shows that whole week rather than a single day.
const buildDayUrl = (calendarUrl: string, date: string) => {
  const compact = date.replace(/-/g, '');
  return `${calendarUrl}&dates=${compact}/${compact}`;
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
