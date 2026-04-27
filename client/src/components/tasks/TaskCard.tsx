import { ChevronLeftIcon, ChevronRightIcon } from '../icons';
import { pendingFor } from '../../lib/utils';
import styles from './Tasks.module.css';
import { TaskRow } from './TaskRow';
import type { TaskCardProps } from './Tasks.shared';

const CARD_LIMIT = 10;

export const TaskCard = ({
  data,
  list,
  filter,
  expanded,
  toggleExpanded,
  openList,
  act,
  openDetail,
}: TaskCardProps) => {
  const pending = pendingFor(data, list.id, filter);
  if (!pending.length) return null;

  const overflow = pending.length > CARD_LIMIT;
  const visible = overflow && !expanded ? pending.slice(0, CARD_LIMIT) : pending;

  return (
    <div className={styles.card}>
      <div className={styles.cardHeader} onClick={openList}>
        <span className={styles.cardTitle}>{list.name}</span>
        <span className={styles.cardCount}>{pending.length}</span>
      </div>

      <div className={styles.cardBody}>
        {visible.map(task => (
          <TaskRow key={task.id} data={data} task={task} listName={list.name} act={act} openDetail={openDetail} />
        ))}
      </div>

      {overflow && (
        <button className={styles.cardOverflowToggle} onClick={toggleExpanded}>
          {expanded ? <ChevronLeftIcon /> : <ChevronRightIcon />}
          {expanded ? ` hide ${pending.length - CARD_LIMIT}` : ` ${pending.length - CARD_LIMIT} more`}
        </button>
      )}
    </div>
  );
};
