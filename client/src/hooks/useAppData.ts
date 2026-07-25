import { useCallback, useEffect, useState } from 'react';
import { api } from '../lib/api';
import type { StateResponse } from '../lib/types';


export const useAppData = () => {
  const [data, setData] = useState<StateResponse | null>(null);
  const [calendarUrl, setCalendarUrl] = useState('');
  const [loading, setLoading] = useState(true);

  const refresh = useCallback(async () => {
    setData(await api.state());
  }, []);

  const act = useCallback(async (path: string, body: unknown) => {
    const res = await api.post(path, body);

    if (res?.ok) {
      setData(await api.state());
      return true;
    }

    return false;
  }, []);

  useEffect(() => {
    const syncConfig = async () => {
      try {
        const browserTimezone = Intl.DateTimeFormat().resolvedOptions().timeZone;
        let config = await api.config();

        if (config && browserTimezone && browserTimezone !== config.calendarTimezone) {
          const res = await api.setTimezone(browserTimezone);
          if (res?.ok) {
            config = await api.config();
          }
        }

        setCalendarUrl(config?.calendarUrl || '');
        setData(await api.state());
      } finally {
        setLoading(false);
      }
    };

    syncConfig();
  }, []);

  useEffect(() => {
    const onVisible = () => {
      if (document.visibilityState === 'visible') {
        refresh();
      }
    };

    document.addEventListener('visibilitychange', onVisible);
    return () => document.removeEventListener('visibilitychange', onVisible);
  }, [refresh]);

  const logout = useCallback(async () => {
    await api.logout();
  }, []);

  return { data, calendarUrl, loading, act, refresh, logout };
};
