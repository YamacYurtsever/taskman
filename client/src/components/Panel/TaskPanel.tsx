import { useCallback, useEffect, useRef, useState } from 'react';
import { API } from '../../lib/api';
import { CHECKBOX_LINE, renderMarkdown } from '../../lib/markdown';
import type { Task, TaskList } from '../../lib/types';
import { cx, formatDue } from '../../lib/utils';
import type { Action } from '../tasks/Tasks.shared';
import dueStyles from '../tasks/DueDate.module.css';
import styles from './TaskPanel.module.css';

type TaskPanelHeaderProps = {
  task: Task;
  list: TaskList;
  today: string;
};

const TaskPanelHeader = ({ task, list, today }: TaskPanelHeaderProps) => {
  const dueInfo = task.due ? formatDue(task.due, today) : null;

  return (
    <>
      <h2 className={styles.taskName}>{task.name}</h2>
      <span className={styles.listName}>{list.name}</span>
      {dueInfo && (
        <span className={cx(styles.due, dueInfo.cls && dueStyles[dueInfo.cls])}>
          {dueInfo.label}
        </span>
      )}
    </>
  );
};

type TaskPanelBodyProps = {
  task: Task;
  act: Action;
};

const TaskPanelBody = ({ task, act }: TaskPanelBodyProps) => {
  const [prevTaskId, setPrevTaskId] = useState(task.id);
  const [isEditing, setIsEditing] = useState(false);
  const [localDesc, setLocalDesc] = useState(task.description);
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const taskIdRef = useRef(task.id);

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

  const toggleCheckbox = useCallback((lineIdx: number) => {
    setLocalDesc(prev => {
      const lines = prev.split('\n');
      const match = lines[lineIdx]?.match(CHECKBOX_LINE);
      if (!match) return prev;
      const [, indent, mark, rest] = match;
      lines[lineIdx] = `${indent}- [${mark.toLowerCase() === 'x' ? ' ' : 'x'}] ${rest}`;
      const newDesc = lines.join('\n');
      if (timerRef.current) clearTimeout(timerRef.current);
      act(API.taskDescription, { taskId: taskIdRef.current, description: newDesc });
      return newDesc;
    });
  }, [act]);

  const descriptionNodes = renderMarkdown(localDesc, {
    linkClassName: styles.link,
    checkboxLineClassName: styles.checkboxLine,
    onToggleCheckbox: toggleCheckbox,
  });

  return (
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
  );
};

export { TaskPanelHeader, TaskPanelBody };
