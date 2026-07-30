import { useCallback, useEffect, useRef, useState } from 'react';
import { api } from '../../lib/api';
import type { NextEvent } from '../../lib/types';
import { CalendarIcon } from '../icons';
import styles from './NextEventPill.module.css';

const POLL_MS = 60_000;
const TICK_MS = 30_000;
const COUNTDOWN_THRESHOLD_MS = 60 * 60 * 1000;

const formatCountdown = (ms: number) => `in ${Math.max(1, Math.round(ms / 60_000))} min`;

const NextEventPill = () => {
  const [event, setEvent] = useState<NextEvent | null>(null);
  const [now, setNow] = useState(() => Date.now());
  const eventTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const refresh = useCallback(async () => {
    const res = await api.nextEvent();
    setEvent(res?.event ?? null);
  }, []);

  useEffect(() => {
    refresh();
    const interval = setInterval(refresh, POLL_MS);
    const onVisible = () => {
      if (document.visibilityState === 'visible') refresh();
    };
    document.addEventListener('visibilitychange', onVisible);
    return () => {
      clearInterval(interval);
      document.removeEventListener('visibilitychange', onVisible);
    };
  }, [refresh]);

  // Refetch right when the current next-event starts, so the pill advances to
  // whatever comes after it promptly instead of waiting for the next poll.
  useEffect(() => {
    if (eventTimerRef.current) clearTimeout(eventTimerRef.current);
    if (!event) return undefined;

    const msUntilStart = new Date(event.startIso).getTime() - Date.now();
    if (msUntilStart <= 0) return undefined;

    eventTimerRef.current = setTimeout(refresh, msUntilStart);
    return () => {
      if (eventTimerRef.current) clearTimeout(eventTimerRef.current);
    };
  }, [event, refresh]);

  useEffect(() => {
    if (!event || event.allDay) return undefined;
    const tick = setInterval(() => setNow(Date.now()), TICK_MS);
    return () => clearInterval(tick);
  }, [event]);

  if (!event) return null;

  const msUntilStart = new Date(event.startIso).getTime() - now;
  const showCountdown = !event.allDay && msUntilStart > 0 && msUntilStart < COUNTDOWN_THRESHOLD_MS;
  const label = event.allDay ? 'All day' : showCountdown ? formatCountdown(msUntilStart) : event.startTime;

  return (
    <div className={styles.pill} title={event.title}>
      <CalendarIcon size={14} />
      <span className={styles.text}>
        <span className={styles.title}>{event.title}</span>
        <span className={styles.time}>{label}</span>
      </span>
    </div>
  );
};

export { NextEventPill };
