import { useState } from 'react';
import type { KeyboardEvent } from 'react';
import { CheckIcon, ContinueIcon, DeleteIcon, DuplicateIcon, EditIcon, MoveIcon, NoteIcon } from '../icons';
import { API } from '../../lib/api';
import { cx, formatDue, sortByName } from '../../lib/utils';
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
  const [newList, setNewList] = useState(listName);
  const dueInfo = task.due ? formatDue(task.due, data.today) : null;

  const saveEdit = async () => {
    const newName = name.trim();
    if (!newName) return;

    await act(API.edit, { list: listName, name: task.name, newName, due: due || null });
    setMode('view');
  };

  const saveMove = async () => {
    if (newList && newList !== listName) {
      await act(API.moveTask, { list: listName, name: task.name, newList });
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
    <div className={cx(styles.taskRow, task.doneAt && styles.done)}>
      <div className={styles.taskLeft}>
        <div
          className={styles.taskCheck}
          title={task.doneAt ? 'Mark pending' : 'Mark done'}
          onClick={() =>
            task.doneAt
              ? act(API.undo, { list: listName, name: task.name })
              : act(API.done, { list: listName, name: task.name })
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
        </div>
        {!task.doneAt && (
          <button
            className="action-btn cnt"
            title="Log continue"
            onClick={() => act(API.continue, { list: listName, task: task.name })}
          >
            <ContinueIcon />
          </button>
        )}
      </div>

      <div className={styles.taskBody} onClick={() => openDetail(task)}>
        <div className={styles.taskNameRow}>
          <span className={styles.taskName}>{task.name}</span>
          {task.description && <NoteIcon className={styles.noteIcon} />}
        </div>
        {dueInfo && (
          <span className={cx(styles.taskDue, dueInfo.cls && styles[dueInfo.cls])}>
            {dueInfo.label}
          </span>
        )}
      </div>

      <div className={styles.taskRight}>
        <div className={styles.taskEditActions}>
          <button className="action-btn mov" title="Move to list" onClick={() => setMode('move')}>
            <MoveIcon />
          </button>
          <button className="action-btn edt" title="Rename" onClick={() => setMode('edit')}>
            <EditIcon />
          </button>
          <button
            className="action-btn dup"
            title="Duplicate"
            onClick={() => act(API.duplicate, { list: listName, name: task.name })}
          >
            <DuplicateIcon />
          </button>
        </div>
        <button
          className="action-btn del"
          title="Delete"
          onClick={() => {
            if (confirm(`Delete "${task.name}"?`)) {
              act(API.delete, { list: listName, name: task.name });
            }
          }}
        >
          <DeleteIcon />
        </button>
      </div>
    </div>
  );
};
