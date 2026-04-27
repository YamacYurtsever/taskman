import { useCallback, useEffect, useRef, useState } from 'react';
import type { ReactNode } from 'react';
import { API } from '../../lib/api';
import type { Task, TaskList } from '../../lib/types';
import { cx, formatDue } from '../../lib/utils';
import type { Action } from './Tasks.shared';
import styles from './TaskDetail.module.css';

type TaskDetailProps = {
  task: Task;
  list: TaskList;
  today: string;
  act: Action;
  onClose: () => void;
};

function renderWithLinks(text: string): ReactNode[] {
  const result: ReactNode[] = [];
  const lines = text.split('\n');

  lines.forEach((line, lineIdx) => {
    if (lineIdx > 0) result.push(<br key={`br-${lineIdx}`} />);

    const urlRegex = /https?:\/\/[^\s]+/g;
    let lastIndex = 0;
    let match: RegExpExecArray | null;
    const lineNodes: ReactNode[] = [];

    while ((match = urlRegex.exec(line)) !== null) {
      if (match.index > lastIndex) {
        lineNodes.push(line.slice(lastIndex, match.index));
      }
      lineNodes.push(
        <a
          key={`${lineIdx}-${match.index}`}
          href={match[0]}
          target="_blank"
          rel="noopener noreferrer"
          className={styles.link}
          onClick={e => e.stopPropagation()}
        >
          {match[0]}
        </a>,
      );
      lastIndex = match.index + match[0].length;
    }

    if (lastIndex < line.length) lineNodes.push(line.slice(lastIndex));
    result.push(...(lineNodes.length > 0 ? lineNodes : [line]));
  });

  return result;
}

export const TaskDetail = ({ task, list, today, act, onClose }: TaskDetailProps) => {
  const [prevTaskId, setPrevTaskId] = useState(task.id);
  const [isEditing, setIsEditing] = useState(false);
  const [localDesc, setLocalDesc] = useState(task.description);
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const listNameRef = useRef(list.name);
  const taskNameRef = useRef(task.name);
  const dueInfo = task.due ? formatDue(task.due, today) : null;

  useEffect(() => {
    listNameRef.current = list.name;
    taskNameRef.current = task.name;
  });

  if (prevTaskId !== task.id) {
    setPrevTaskId(task.id);
    setLocalDesc(task.description);
    setIsEditing(false);
  }

  useEffect(() => {
    return () => {
      if (timerRef.current) clearTimeout(timerRef.current);
    };
  }, []);

  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.key !== 'Escape') return;
      const target = e.target as HTMLElement;
      if (target.closest('[data-task-edit]')) return;
      onClose();
    };
    document.addEventListener('keydown', handler);
    return () => document.removeEventListener('keydown', handler);
  }, [onClose]);

  const scheduleSave = useCallback((value: string) => {
    if (timerRef.current) clearTimeout(timerRef.current);
    timerRef.current = setTimeout(() => {
      act(API.taskDescription, {
        list: listNameRef.current,
        name: taskNameRef.current,
        description: value,
      });
    }, 600);
  }, [act]);

  const handleChange = (value: string) => {
    setLocalDesc(value);
    scheduleSave(value);
  };

  return (
    <div className={styles.panel}>
      <div className={styles.header}>
        <div className={styles.meta}>
          <span className={styles.listName}>{list.name}</span>
          {dueInfo && (
            <span className={cx(styles.due, dueInfo.cls ? styles[dueInfo.cls as keyof typeof styles] : undefined)}>
              {dueInfo.label}
            </span>
          )}
        </div>
        <button className={styles.closeBtn} onClick={onClose} title="Close (Esc)">✕</button>
      </div>

      <h2 className={styles.taskName}>{task.name}</h2>

      <div className={styles.descriptionArea}>
        {isEditing ? (
          <textarea
            autoFocus
            className={styles.textarea}
            value={localDesc}
            onChange={e => handleChange(e.target.value)}
            onBlur={() => setIsEditing(false)}
            placeholder="Add a description..."
          />
        ) : (
          <div
            className={cx(styles.descView, !localDesc && styles.descPlaceholder)}
            onClick={() => setIsEditing(true)}
          >
            {localDesc ? renderWithLinks(localDesc) : 'Add a description...'}
          </div>
        )}
      </div>
    </div>
  );
};
