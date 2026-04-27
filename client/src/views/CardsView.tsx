import type { ReactElement } from 'react';
import { useState } from 'react';
import { TaskCard } from '../components/tasks/TaskCard';
import type { CardsViewProps } from '../components/tasks/Tasks.shared';
import { cx, MSG, pendingFor, sortByName } from '../lib/utils';
import styles from '../components/tasks/Tasks.module.css';

export const CardsView = ({
  data,
  filter,
  selectedGroup,
  selectGroup,
  selectList,
  act,
  openDetail,
}: CardsViewProps) => {
  const [expandedCards, setExpandedCards] = useState(new Set<string>());

  const toggleExpanded = (id: string) => {
    const next = new Set(expandedCards);
    if (next.has(id)) {
      next.delete(id);
    } else {
      next.add(id);
    }
    setExpandedCards(next);
  };

  const renderCards = (lists: typeof data.lists) =>
    lists
      .filter(list => pendingFor(data, list.id, filter).length > 0)
      .map(list => (
        <TaskCard
          key={list.id}
          data={data}
          list={list}
          filter={filter}
          expanded={expandedCards.has(list.id)}
          toggleExpanded={() => toggleExpanded(list.id)}
          openList={() => selectList(list.id)}
          act={act}
          openDetail={openDetail}
        />
      ));

  if (selectedGroup) {
    const group = data.groups.find(item => item.id === selectedGroup);
    if (!group) return null;

    const cards = renderCards(sortByName(data.lists.filter(list => list.groupId === group.id)));
    return (
      <div className={styles.cardsView}>
        <div className={styles.cardsSection}>
          <div className={styles.sectionLabel}>{group.name}</div>
          {cards.length ? <div className={styles.cardsGrid}>{cards}</div> : <div className="empty">{MSG.noTasks}</div>}
        </div>
      </div>
    );
  }

  const sections: ReactElement[] = [];
  const seen = new Set<string>();

  for (const group of sortByName(data.groups)) {
    const lists = sortByName(data.lists.filter(list => list.groupId === group.id));
    const cards = renderCards(lists);

    if (cards.length) {
      sections.push(
        <div key={group.id} className={styles.cardsSection}>
          <div
            className={cx(styles.sectionLabel, styles.sectionLabelLink)}
            onClick={() => selectGroup(group.id)}
          >
            {group.name}
          </div>
          <div className={styles.cardsGrid}>
            {cards}
          </div>
        </div>,
      );
    }

    lists.forEach(list => seen.add(list.id));
  }

  const ungrouped = sortByName(data.lists.filter(list => !seen.has(list.id)));
  const ungroupedCards = renderCards(ungrouped);

  if (ungroupedCards.length) {
    const hasGroups = data.groups.some(group => data.lists.some(list => list.groupId === group.id));
    sections.push(
      <div key="others" className={styles.cardsSection}>
        {hasGroups && <div className={styles.sectionLabel}>{MSG.others}</div>}
        <div className={styles.cardsGrid}>
          {ungroupedCards}
        </div>
      </div>,
    );
  }

  return sections.length ? <div className={styles.cardsView}>{sections}</div> : <div className="empty">{MSG.noTasks}</div>;
};
