import { useState } from 'react';
import type { KeyboardEvent } from 'react';
import { API } from '../../lib/api';
import type { Group } from '../../lib/types';
import { cx, stop } from '../../lib/utils';
import { CheckIcon, DeleteIcon, EditIcon } from '../icons';
import styles from './Sidebar.module.css';
import type { Action } from './Sidebar.shared';

type SidebarGroupRowProps = {
  group: Group;
  active: boolean;
  selectGroup: () => void;
  act: Action;
};

const submitOnEnter =
  (save: () => void, cancel: () => void) =>
  (e: KeyboardEvent) => {
    if (e.key === 'Enter') save();
    if (e.key === 'Escape') cancel();
  };

const activateOnKey = (onClick: () => void) => (e: KeyboardEvent) => {
  if (e.key === 'Enter' || e.key === ' ') {
    e.preventDefault();
    onClick();
  }
};

const SaveAction = ({ onClick }: { onClick: () => void }) => (
  <div className={styles.right}>
    <div className={styles.actions}>
      <button className="action-btn sav" title="Save" onClick={onClick}>
        <CheckIcon />
      </button>
    </div>
  </div>
);

const SidebarGroupRow = ({
  group,
  active,
  selectGroup,
  act,
}: SidebarGroupRowProps) => {
  const [renaming, setRenaming] = useState(false);
  const [name, setName] = useState(group.name);

  const cancel = () => setRenaming(false);

  const save = () => {
    const newName = name.trim();

    if (newName && newName !== group.name) {
      act(API.renameGroup, { group: group.name, newName });
    } else {
      cancel();
    }
  };

  if (renaming) {
    return (
      <div className={cx(styles.navItem, styles.navGroupHeader, styles.renameRow)}>
        <input
          autoFocus
          autoComplete="off"
          value={name}
          onChange={e => setName(e.target.value)}
          onKeyDown={submitOnEnter(save, cancel)}
        />

        <SaveAction onClick={save} />
      </div>
    );
  }

  return (
    <div
      role="button"
      tabIndex={0}
      className={cx(styles.navItem, styles.navGroupHeader, active && styles.active)}
      onClick={selectGroup}
      onKeyDown={activateOnKey(selectGroup)}
    >
      {group.name}

      <div className={cx(styles.actions, styles.groupActions)}>
        <button
          className="action-btn edt"
          title="Rename"
          onClick={stop(() => setRenaming(true))}
        >
          <EditIcon />
        </button>

        <button
          className="action-btn del"
          title="Delete group"
          onClick={stop(() => {
            if (confirm(`Delete group "${group.name}"? Lists will be ungrouped.`)) {
              act(API.deleteGroup, { group: group.name });
            }
          })}
        >
          <DeleteIcon />
        </button>
      </div>
    </div>
  );
};

export { SidebarGroupRow };
