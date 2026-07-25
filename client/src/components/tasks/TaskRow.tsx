import { useState } from 'react';
import type { CSSProperties, KeyboardEvent } from 'react';
import { CheckIcon, ContinueIcon, DeleteIcon, DuplicateIcon, EditIcon, MoveIcon, NoteIcon, RepeatIcon } from '../icons';
import { API } from '../../lib/api';
import { cx, formatDue, sortByName } from '../../lib/utils';
import dueStyles from './DueDate.module.css';
import styles from './Tasks.module.css';
import type { TaskRowProps } from './Tasks.shared';

const submitOnEnter =
  (save: () => void, cancel: () => void) =>
  (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') save();
    if (e.key === 'Escape') cancel();
  };

const SaveAction = ({ onClick }: { onClick: () => void }) => (
  <div className={styles.taskRight}>
    <button className="action-btn sav" title="Save" onClick={onClick}>
      <CheckIcon />
    </button>
  </div>
);

export const TaskRow = ({ data, task, listName, act, openDetail }: TaskRowProps) => {
  const [mode, setMode] = useState<'view' | 'edit' | 'move'>('view');
  const [name, setName] = useState(task.name);
  const [due, setDue] = useState(task.due || '');
  const [recur, setRecur] = useState(String(task.recurIntervalDays ?? ''));
  const [newList, setNewList] = useState(listName);
  const dueInfo = task.due ? formatDue(task.due, data.today) : null;
  const flagColorVar =
    dueInfo?.cls === 'due-overdue'
      ? '--red'
      : dueInfo?.cls === 'due-today'
        ? '--accent-hl'
        : dueInfo?.cls === 'due-upcoming'
          ? '--accent'
          : null;

  const saveEdit = async () => {
    const newName = name.trim();
    if (!newName) return;

    const recurTrimmed = recur.trim();
    await act(API.edit, {
      taskId: task.id,
      newName,
      due: due || null,
      recurIntervalDays: recurTrimmed ? Number(recurTrimmed) : null,
    });
    setMode('view');
  };

  const saveMove = async () => {
    if (newList && newList !== listName) {
      await act(API.moveTask, { taskId: task.id, newList });
    }

    setMode('view');
  };

  if (mode === 'edit') {
    return (
      <div className={cx(styles.taskRow, styles.taskEditRow)} data-task-edit="">
        <div className={styles.taskLeft} />
        <div className={styles.taskEditBody}>
          <input
            autoFocus
            autoComplete="off"
            className={styles.taskEditName}
            value={name}
            onChange={e => setName(e.target.value)}
            onKeyDown={submitOnEnter(saveEdit, () => setMode('view'))}
          />
          <input
            className={styles.taskEditDue}
            type="date"
            value={due}
            onChange={e => setDue(e.target.value)}
          />
          <label className={styles.taskEditRecurGroup} title="Repeat every N days">
            <span className={styles.taskEditRecurLabel}>↻</span>
            <input
              className={styles.taskEditRecur}
              type="number"
              min={1}
              placeholder="—"
              value={recur}
              onChange={e => setRecur(e.target.value)}
            />
          </label>
        </div>
        <SaveAction onClick={saveEdit} />
      </div>
    );
  }

  if (mode === 'move') {
    return (
      <div className={cx(styles.taskRow, styles.taskMoveRow)} data-task-edit="">
        <select
          autoFocus
          className={styles.taskMoveSelect}
          value={newList}
          onChange={e => setNewList(e.target.value)}
        >
          {sortByName(data.lists).map(list => (
            <option key={list.id} value={list.name}>
              {list.name}
            </option>
          ))}
        </select>
        <SaveAction onClick={saveMove} />
      </div>
    );
  }

  return (
    <div
      className={cx(styles.taskRow, task.doneAt && styles.done, task.flagged && styles.flagged)}
      style={
        task.flagged && flagColorVar
          ? ({ borderLeftColor: `var(${flagColorVar})` } as CSSProperties)
          : undefined
      }
      onContextMenu={e => {
        e.preventDefault();
        act(API.flagTask, { taskId: task.id, flagged: !task.flagged });
      }}
    >
      <div className={styles.taskLeft}>
        <button
          type="button"
          className={styles.taskCheck}
          title={task.doneAt ? 'Mark pending' : 'Mark done'}
          onClick={() =>
            task.doneAt
              ? act(API.undo, { taskId: task.id })
              : act(API.done, { taskId: task.id })
          }
        >
          <svg
            className={styles.taskCheckSvg}
            width="9"
            height="9"
            viewBox="0 0 16 16"
            fill="none"
            stroke="#fff"
            strokeWidth="2.5"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <path d="M3 8.5l3 3L13 5" />
          </svg>
        </button>
        {!task.doneAt && (
          <button
            className="action-btn cnt"
            title="Log continue"
            onClick={() => act(API.continue, { taskId: task.id })}
          >
            <ContinueIcon />
          </button>
        )}
      </div>

      <button type="button" className={styles.taskBody} onClick={() => openDetail(task)}>
        <div className={styles.taskNameRow}>
          <span className={styles.taskName}>{task.name}</span>
          {(task.description || task.recurIntervalDays) && (
            <div className={styles.taskIcons}>
              {task.recurIntervalDays && (
                <span
                  title={`Repeats every ${task.recurIntervalDays} day${task.recurIntervalDays === 1 ? '' : 's'}`}
                >
                  <RepeatIcon className={styles.repeatIcon} />
                </span>
              )}
              {task.description && <NoteIcon className={styles.noteIcon} />}
            </div>
          )}
        </div>
        {dueInfo && (
          <span className={cx(styles.taskDue, dueInfo.cls && dueStyles[dueInfo.cls])}>
            {dueInfo.label}
          </span>
        )}
      </button>

      <div className={styles.taskRight}>
        <div className={styles.taskEditActions}>
          <button className="action-btn mov" title="Move to list" onClick={() => setMode('move')}>
            <MoveIcon />
          </button>
          <button className="action-btn edt" title="Rename" onClick={() => setMode('edit')}>
            <EditIcon />
          </button>
        </div>
        <div className={styles.taskEditActions}>
          <button
            className="action-btn dup"
            title="Duplicate"
            onClick={() => act(API.duplicate, { taskId: task.id })}
          >
            <DuplicateIcon />
          </button>
          <button
            className="action-btn del"
            title="Delete"
            onClick={() => {
              if (confirm(`Delete "${task.name}"?`)) {
                act(API.delete, { taskId: task.id });
              }
            }}
          >
            <DeleteIcon />
          </button>
        </div>
      </div>
    </div>
  );
};
