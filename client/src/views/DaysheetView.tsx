import { useCallback, useEffect, useRef, useState } from 'react';
import {
  CheckIcon,
  ChevronLeftIcon,
  ChevronRightIcon,
  DeleteIcon,
  EditIcon,
  PlusIcon,
} from '../components/icons';
import { API, api } from '../lib/api';
import type { DaysheetEntry, DaysheetResponse, StateResponse } from '../lib/types';
import { MSG, sortByName, todayStr } from '../lib/utils';
import styles from './DaysheetView.module.css';

type Action = (path: string, body: unknown) => Promise<void>;

type DaysheetViewProps = {
  data: StateResponse | null;
  act: Action;
  refresh: () => Promise<void>;
};

type TimelineProps = {
  entries: DaysheetEntry[];
  act: Action;
  refresh: () => Promise<void>;
};

type TimelineEntryProps = {
  entry: DaysheetEntry;
  inGroup: boolean;
  act: Action;
  refresh: () => Promise<void>;
};

type LogFormProps = {
  lists: StateResponse['lists'];
  act: Action;
};

const DaysheetView = ({ data, act, refresh }: DaysheetViewProps) => {
  const [date, setDate] = useState(todayStr());
  const [daysheet, setDaysheet] = useState<DaysheetResponse | null>(null);
  const dateInputRef = useRef<HTMLInputElement>(null);

  const fetchDaysheet = useCallback(async (date: string) => {
    setDaysheet(await api.daysheet(date));
  }, []);

  useEffect(() => {
    fetchDaysheet(date);
  }, [date, fetchDaysheet]);

  const localAct = useCallback(
    async (path: string, body: unknown) => {
      await act(path, body);
      await fetchDaysheet(date);
    },
    [act, fetchDaysheet, date],
  );

  const localRefresh = useCallback(async () => {
    await Promise.all([refresh(), fetchDaysheet(date)]);
  }, [refresh, fetchDaysheet, date]);

  const shiftDay = (delta: number) => {
    const next = parseLocalDate(date);
    next.setDate(next.getDate() + delta);
    setDate(dateString(next));
  };

  const openDatePicker = () => {
    const input = dateInputRef.current;
    if (!input) return;

    const pickerInput = input as HTMLInputElement & { showPicker?: () => void };
    if (pickerInput.showPicker) {
      pickerInput.showPicker();
      return;
    }

    input.focus();
    input.click();
  };

  const entries = daysheet?.entries ?? [];
  const lists = data?.lists ?? [];

  return (
    <div className={styles.daysheetView}>
      <div className={styles.daysheetHeader}>
        <h1 className={styles.daysheetTitle}>{MSG.daysheet}</h1>

        <div className={styles.dateNav}>
          <button className={styles.dateNavBtn} onClick={() => shiftDay(-1)}>
            <ChevronLeftIcon />
          </button>

          <button className={styles.dateNavLabel} onClick={openDatePicker}>
            {dateLabel(date)}
          </button>

          <input
            ref={dateInputRef}
            className={styles.dateNavPicker}
            type="date"
            value={date}
            onChange={e => setDate(e.target.value)}
            tabIndex={-1}
            aria-hidden="true"
          />

          <button className={styles.dateNavBtn} onClick={() => shiftDay(1)}>
            <ChevronRightIcon />
          </button>
        </div>
      </div>

      <Timeline entries={entries} act={localAct} refresh={localRefresh} />

      {lists.length > 0 && <LogForm lists={lists} act={localAct} />}
    </div>
  );
};

const Timeline = ({ entries, act, refresh }: TimelineProps) => {
  if (!entries.length) {
    return (
      <div className={styles.timeline}>
        <div className="empty">{MSG.noEntries}</div>
      </div>
    );
  }

  return (
    <div className={styles.timeline}>
      {groupEntries(entries).map(section => (
        <div key={section.id} className={styles.timelineGroup}>
          <div className={styles.timelineGroupName}>{section.name}</div>

          {section.items.map(entry => (
            <TimelineEntry
              key={entry.id}
              entry={entry}
              inGroup={section.inGroup}
              act={act}
              refresh={refresh}
            />
          ))}
        </div>
      ))}
    </div>
  );
};

const TimelineEntry = ({ entry, inGroup, act, refresh }: TimelineEntryProps) => {
  const [editing, setEditing] = useState(false);
  const [text, setText] = useState(entry.text);

  const save = async () => {
    const newText = text.trim();
    if (!newText) return;

    await act(API.daysheetEdit, { id: entry.id, text: newText });
    setEditing(false);
  };

  if (editing) {
    return (
      <div className={`${styles.timelineEntry} ${styles.timelineEditRow}`}>
        <span className={styles.timelineTime}>{entry.datetime.slice(11, 16)}</span>

        <input
          autoFocus
          autoComplete="off"
          className={styles.timelineEditInput}
          value={text}
          onChange={e => setText(e.target.value)}
          onKeyDown={e => {
            if (e.key === 'Enter') save();
            if (e.key === 'Escape') refresh();
          }}
        />

        <div className={styles.timelineActions}>
          <button className={`action-btn sav ${styles.timelineAction}`} title="Save" onClick={save}>
            <CheckIcon />
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className={styles.timelineEntry}>
      <span className={styles.timelineTime}>{entry.datetime.slice(11, 16)}</span>

      <span className={styles.timelineText}>
        {entryPrefix(entry.type)}
        {entry.text}
        {inGroup && <span className={styles.timelineListTag}>{entry.listName}</span>}
      </span>

      <div className={styles.timelineActions}>
        {entry.type === 'log' && (
          <button
            className={`action-btn edt ${styles.timelineAction}`}
            title="Edit"
            onClick={() => setEditing(true)}
          >
            <EditIcon />
          </button>
        )}

        <button
          className={`action-btn del ${styles.timelineAction}`}
          title="Delete"
          onClick={() => act(API.daysheetDelete, { id: entry.id })}
        >
          <DeleteIcon />
        </button>
      </div>
    </div>
  );
};

const LogForm = ({ lists, act }: LogFormProps) => {
  const sorted = sortByName(lists);
  const [listName, setListName] = useState(sorted[0]?.name ?? '');
  const [text, setText] = useState('');

  const submit = () => {
    const trimmed = text.trim();
    if (!trimmed) return;

    act(API.log, { list: listName, text: trimmed });
    setText('');
  };

  return (
    <div className={styles.logForm}>
      <select value={listName} onChange={e => setListName(e.target.value)}>
        {sorted.map(list => (
          <option key={list.id} value={list.name}>
            {list.name}
          </option>
        ))}
      </select>

      <input
        type="text"
        autoComplete="off"
        placeholder={MSG.entryText}
        value={text}
        onChange={e => setText(e.target.value)}
        onKeyDown={e => e.key === 'Enter' && submit()}
      />

      <button className={styles.logFormBtn} onClick={submit}>
        <PlusIcon />
      </button>
    </div>
  );
};

const dateString = (date: Date) =>
  date.toISOString().slice(0, 10);

const parseLocalDate = (date: string) =>
  new Date(`${date}T12:00:00`);

const dateLabel = (date: string) => {
  const today = todayStr();
  if (date === today) return MSG.today;

  const yesterday = new Date();
  yesterday.setDate(yesterday.getDate() - 1);
  if (date === dateString(yesterday)) return MSG.yesterday;

  return parseLocalDate(date).toLocaleDateString(undefined, {
    month: 'short',
    day: 'numeric',
  });
};

const entryPrefix = (type: DaysheetEntry['type']) => {
  if (type === 'done') return 'Finished ';
  if (type === 'continue') return 'Continued ';
  return '';
};

const groupEntries = (entries: DaysheetEntry[]) => {
  const sections = new Map<
    string,
    { id: string; name: string; inGroup: boolean; items: DaysheetEntry[] }
  >();

  for (const entry of entries) {
    if (!sections.has(entry.sectionId)) {
      sections.set(entry.sectionId, {
        id: entry.sectionId,
        name: entry.sectionName,
        inGroup: entry.inGroup,
        items: [],
      });
    }

    sections.get(entry.sectionId)?.items.push(entry);
  }

  return sortByName([...sections.values()]);
};

export { DaysheetView };
