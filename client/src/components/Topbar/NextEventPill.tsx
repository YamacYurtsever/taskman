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

  // Refetch right when the current next-event ends, so the pill advances to
  // whatever comes after it promptly instead of waiting for the next poll —
  // while active, this event stays "the next event" so there's nothing to
  // refetch until it's over.
  useEffect(() => {
    if (eventTimerRef.current) clearTimeout(eventTimerRef.current);
    if (!event) return undefined;

    const msUntilEnd = new Date(event.endIso).getTime() - Date.now();
    if (msUntilEnd <= 0) return undefined;

    eventTimerRef.current = setTimeout(refresh, msUntilEnd);
    return () => {
      if (eventTimerRef.current) clearTimeout(eventTimerRef.current);
    };
  }, [event, refresh]);

  useEffect(() => {
    if (!event) return undefined;
    const tick = setInterval(() => setNow(Date.now()), TICK_MS);
    return () => clearInterval(tick);
  }, [event]);

  if (!event) return null;

  const msUntilStart = new Date(event.startIso).getTime() - now;
  const msUntilEnd = new Date(event.endIso).getTime() - now;
  const isActive = msUntilStart <= 0 && msUntilEnd > 0;
  const showCountdown = !isActive && msUntilStart > 0 && msUntilStart < COUNTDOWN_THRESHOLD_MS;
  const label = isActive
    ? 'Active'
    : showCountdown
      ? formatCountdown(msUntilStart)
      : `${event.startTime} – ${event.endTime}`;

  return (
    <div className={styles.pill} title={event.title}>
      <CalendarIcon size={14} className={isActive ? styles.iconActive : undefined} />
      <span className={styles.text}>
        <span className={styles.title}>{event.title}</span>
        <span className={isActive ? styles.timeActive : styles.time}>{label}</span>
      </span>
    </div>
  );
};

export { NextEventPill };
