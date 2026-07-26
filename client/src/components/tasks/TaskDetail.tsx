import { useCallback, useEffect, useRef, useState } from 'react';
import type { ReactNode } from 'react';
import { API } from '../../lib/api';
import type { Task, TaskList } from '../../lib/types';
import { cx, formatDue } from '../../lib/utils';
import type { Action } from './Tasks.shared';
import dueStyles from './DueDate.module.css';
import styles from './TaskDetail.module.css';

type TaskDetailProps = {
  task: Task;
  list: TaskList;
  today: string;
  act: Action;
  onClose: () => void;
};

const CHECKBOX_LINE = /^(\s*)-\s\[([ xX])\]\s(.*)$/;

function renderLineWithLinks(line: string, lineIdx: number): ReactNode[] {
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
  return lineNodes.length > 0 ? lineNodes : [line];
}

export const TaskDetail = ({ task, list, today, act, onClose }: TaskDetailProps) => {
  const [prevTaskId, setPrevTaskId] = useState(task.id);
  const [isEditing, setIsEditing] = useState(false);
  const [localDesc, setLocalDesc] = useState(task.description);
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const taskIdRef = useRef(task.id);
  const dueInfo = task.due ? formatDue(task.due, today) : null;

  useEffect(() => {
    taskIdRef.current = task.id;
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
        taskId: taskIdRef.current,
        description: value,
      });
    }, 600);
  }, [act]);

  const handleChange = (value: string) => {
    setLocalDesc(value);
    scheduleSave(value);
  };

  const toggleCheckbox = (lineIdx: number) => {
    const lines = localDesc.split('\n');
    const match = lines[lineIdx]?.match(CHECKBOX_LINE);
    if (!match) return;
    const [, indent, mark, rest] = match;
    lines[lineIdx] = `${indent}- [${mark.toLowerCase() === 'x' ? ' ' : 'x'}] ${rest}`;
    handleChange(lines.join('\n'));
  };

  const descriptionNodes: ReactNode[] = [];
  localDesc.split('\n').forEach((line, lineIdx) => {
    if (lineIdx > 0) descriptionNodes.push(<br key={`br-${lineIdx}`} />);

    const checkboxMatch = line.match(CHECKBOX_LINE);
    if (checkboxMatch) {
      const [, indent, mark, rest] = checkboxMatch;
      descriptionNodes.push(
        <label
          key={`line-${lineIdx}`}
          className={styles.checkboxLine}
          style={indent ? { marginLeft: `${indent.length * 0.6}em` } : undefined}
        >
          <input
            type="checkbox"
            checked={mark.toLowerCase() === 'x'}
            onChange={() => toggleCheckbox(lineIdx)}
            onClick={e => e.stopPropagation()}
          />
          {renderLineWithLinks(rest, lineIdx)}
        </label>,
      );
      return;
    }

    descriptionNodes.push(...renderLineWithLinks(line, lineIdx));
  });

  return (
    <div className={styles.panel}>
      <div className={styles.header}>
        <div className={styles.meta}>
          <span className={styles.listName}>{list.name}</span>
          {dueInfo && (
            <span className={cx(styles.due, dueInfo.cls && dueStyles[dueInfo.cls])}>
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
            {localDesc ? descriptionNodes : 'Add a description...'}
          </div>
        )}
      </div>
    </div>
  );
};
