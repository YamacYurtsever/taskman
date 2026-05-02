import { useState } from 'react';
import { AddTaskForm } from '../components/tasks/AddTaskForm';
import { TaskRow } from '../components/tasks/TaskRow';
import type { FocusedViewProps } from '../components/tasks/Tasks.shared';
import { ChevronLeftIcon, ChevronRightIcon, PinFilledIcon, PinIcon } from '../components/icons';
import { API } from '../lib/api';
import { doneFor, MSG, pendingFor } from '../lib/utils';
import styles from '../components/tasks/Tasks.module.css';

export const FocusedView = ({ data, listId, filter, act, openDetail }: FocusedViewProps) => {
  const [showDone, setShowDone] = useState(false);

  const list = data.lists.find(item => item.id === listId);
  if (!list) return <div className="empty">{MSG.noTasks}</div>;

  const pending = pendingFor(data, listId, filter);
  const done = doneFor(data, listId);

  return (
    <div className={styles.focusedView}>
      <div className={styles.focusedHeader}>
        <h1 className={styles.focusedTitle}>{list.name}</h1>
        <div className={styles.focusedMetaRow}>
          <span className={styles.focusedMeta}>{pending.length}</span>
          <button
            className={`action-btn pin ${list.pinned ? styles.pinBtnActive : ''}`}
            title={list.pinned ? 'Unpin list' : 'Pin list'}
            onClick={() => act(API.pinList, { listId: list.id, pinned: !list.pinned })}
          >
            {list.pinned ? <PinFilledIcon size={14} /> : <PinIcon size={14} />}
          </button>
        </div>
      </div>

      <div className={styles.focusedTasks}>
        {pending.length ? (
          pending.map(task => (
            <TaskRow key={task.id} data={data} task={task} listName={list.name} act={act} openDetail={openDetail} />
          ))
        ) : (
          <div className="empty">{MSG.noTasks}</div>
        )}
      </div>

      <AddTaskForm listName={list.name} act={act} />

      {done.length > 0 && (
        <div className={styles.doneWrapper}>
          <button className={styles.doneToggle} onClick={() => setShowDone(value => !value)}>
            {showDone ? <ChevronLeftIcon /> : <ChevronRightIcon />}
            {` ${showDone ? 'hide' : 'show'} done (${done.length})`}
          </button>

          <div className={styles.doneSection}>
            {showDone &&
              done.map(task => (
                <TaskRow key={task.id} data={data} task={task} listName={list.name} act={act} openDetail={openDetail} />
              ))}
          </div>
        </div>
      )}
    </div>
  );
};
