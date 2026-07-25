import { useState } from 'react';
import { LayersIcon, PlusIcon, RepeatIcon } from '../icons';
import { API } from '../../lib/api';
import { cx, MSG } from '../../lib/utils';
import styles from './Tasks.module.css';
import type { Action } from './Tasks.shared';

type AddTaskFormProps = {
  listName: string;
  act: Action;
};

export const AddTaskForm = ({ listName, act }: AddTaskFormProps) => {
  const [mode, setMode] = useState<'single' | 'batch'>('single');
  const [recurring, setRecurring] = useState(false);
  const [name, setName] = useState('');
  const [due, setDue] = useState('');
  const [intervalDays, setIntervalDays] = useState('1');
  const [count, setCount] = useState('1');

  const submit = async () => {
    const trimmed = name.trim();
    if (!trimmed) return;

    if (mode === 'batch' && recurring) {
      const ok = await act(API.add, {
        list: listName,
        name: trimmed,
        due: due || null,
        recurIntervalDays: Number(intervalDays),
      });
      if (!ok) return;
    } else if (mode === 'batch') {
      const ok = await act(API.addSeries, {
        list: listName,
        name: trimmed,
        startDue: due || null,
        intervalDays: Number(intervalDays),
        count: Number(count),
      });
      if (!ok) return;
    } else {
      await act(API.add, { list: listName, name: trimmed, due: due || null });
    }

    setName('');
    setDue('');
  };

  return (
    <div className={styles.inlineAdd}>
      <button
        type="button"
        className={cx(styles.inlineAddToggle, mode === 'batch' && styles.inlineAddToggleActive)}
        title={mode === 'batch' ? 'Switch to single add' : 'Switch to batch add'}
        onClick={() => setMode(mode === 'batch' ? 'single' : 'batch')}
      >
        <LayersIcon />
      </button>

      <input
        type="text"
        placeholder={MSG.addTask}
        value={name}
        onChange={e => setName(e.target.value)}
        onKeyDown={e => e.key === 'Enter' && submit()}
      />
      <input type="date" value={due} onChange={e => setDue(e.target.value)} />

      <button className={styles.inlineAddBtn} onClick={submit}>
        <PlusIcon />
      </button>

      {mode === 'batch' && (
        <div className={styles.inlineAddSeriesRow}>
          <label className={styles.inlineAddSeriesGroup} title="Days between each task">
            <span className={styles.inlineAddSeriesLabel}>↻</span>
            <input
              className={styles.inlineAddNumber}
              type="number"
              min={1}
              value={intervalDays}
              onChange={e => setIntervalDays(e.target.value)}
            />
          </label>
          <label className={styles.inlineAddSeriesGroup} title="Number of tasks to create">
            <span className={styles.inlineAddSeriesLabel}>×</span>
            <input
              className={styles.inlineAddNumber}
              type="number"
              min={1}
              value={count}
              disabled={recurring}
              onChange={e => setCount(e.target.value)}
            />
          </label>
          <button
            type="button"
            className={cx(styles.inlineAddRecurToggle, recurring && styles.inlineAddToggleActive)}
            title={recurring ? 'Switch to fixed count' : 'Make this a recurring task instead'}
            onClick={() => setRecurring(r => !r)}
          >
            <RepeatIcon />
          </button>
        </div>
      )}
    </div>
  );
};
