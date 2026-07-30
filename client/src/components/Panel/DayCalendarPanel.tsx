import styles from './DayCalendarPanel.module.css';

type DayCalendarPanelBodyProps = {
  calendarUrl: string;
  date: string;
};

const nextDateCompact = (date: string) => {
  const [year, month, day] = date.split('-').map(Number);
  const next = new Date(year, month - 1, day + 1);
  const pad = (n: number) => String(n).padStart(2, '0');
  return `${next.getFullYear()}${pad(next.getMonth() + 1)}${pad(next.getDate())}`;
};

// Google's embed API has no true single-day mode — AGENDA (labeled "Schedule"
// in Google Calendar's own UI) scoped to a one-day range is the closest match.
// A zero-length range (date/date) renders a blank iframe, so this spans a real
// day (date to the following date) instead.
const buildDayUrl = (calendarUrl: string, date: string) => {
  const compact = date.replace(/-/g, '');
  return `${calendarUrl.replace('mode=WEEK', 'mode=AGENDA')}&dates=${compact}/${nextDateCompact(date)}`;
};

const DayCalendarPanelBody = ({ calendarUrl, date }: DayCalendarPanelBodyProps) => {
  if (!calendarUrl) return <div className="empty">No calendar connected</div>;

  return (
    <div className={styles.frameWrap}>
      <iframe className={styles.frame} src={buildDayUrl(calendarUrl, date)} title="Day calendar" />
    </div>
  );
};

export { DayCalendarPanelBody };
