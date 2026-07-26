import { useState } from 'react';
import type { KeyboardEvent } from 'react';
import { API } from '../../lib/api';
import { MSG, cx, sortByName, stop } from '../../lib/utils';
import { CheckIcon, DeleteIcon, EditIcon, MoveIcon } from '../icons';
import styles from './Sidebar.module.css';
import type { Action, ListRowProps, NewItemKind } from './Sidebar.shared';

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

const SaveAction = ({ title, onClick }: { title: string; onClick: () => void }) => (
  <div className={styles.right}>
    <div className={styles.actions}>
      <button className="action-btn sav" title={title} onClick={onClick}>
        <CheckIcon />
      </button>
    </div>
  </div>
);

const SidebarListRow = ({
  dataGroups,
  filterCount,
  isActive,
  isEditing,
  isMoving,
  list,
  onDelete,
  onEdit,
  onMove,
  onSelect,
  act,
  cancel,
}: ListRowProps) => {
  if (isEditing) {
    return <RenameListRow list={list} act={act} cancel={cancel} />;
  }

  if (isMoving) {
    return <MoveListRow list={list} groups={dataGroups} act={act} cancel={cancel} />;
  }

  return (
    <div
      role="button"
      tabIndex={0}
      className={cx(styles.navItem, styles.navList, isActive && styles.active)}
      onClick={onSelect}
      onKeyDown={activateOnKey(onSelect)}
    >
      {list.name}

      <div className={styles.right}>
        <div className={styles.actions}>
          {dataGroups.length > 0 && (
            <button
              className="action-btn mov"
              title="Move to group"
              onClick={stop(onMove)}
            >
              <MoveIcon />
            </button>
          )}

          <button className="action-btn edt" title="Rename" onClick={stop(onEdit)}>
            <EditIcon />
          </button>

          <button className="action-btn del" title="Delete" onClick={stop(onDelete)}>
            <DeleteIcon />
          </button>
        </div>

        {filterCount > 0 && <span className={styles.count}>{filterCount}</span>}
      </div>
    </div>
  );
};

type RenameListRowProps = {
  list: ListRowProps['list'];
  act: Action;
  cancel: () => void;
};

const RenameListRow = ({ list, act, cancel }: RenameListRowProps) => {
  const [name, setName] = useState(list.name);

  const save = async () => {
    const newName = name.trim();

    if (newName && newName !== list.name) {
      if (await act(API.renameList, { list: list.name, newName })) {
        cancel();
      }
    } else {
      cancel();
    }
  };

  return (
    <div className={cx(styles.navItem, styles.navList, styles.renameRow)}>
      <input
        autoFocus
        autoComplete="off"
        value={name}
        onChange={e => setName(e.target.value)}
        onKeyDown={submitOnEnter(save, cancel)}
      />

      <SaveAction title="Save" onClick={save} />
    </div>
  );
};

type MoveListRowProps = {
  list: ListRowProps['list'];
  groups: ListRowProps['dataGroups'];
  act: Action;
  cancel: () => void;
};

const MoveListRow = ({ list, groups, act, cancel }: MoveListRowProps) => {
  const currentGroup = groups.find(group => group.id === list.groupId);
  const [group, setGroup] = useState(currentGroup?.name ?? '');

  const save = async () => {
    await act(API.moveList, { list: list.name, group });
    cancel();
  };

  return (
    <div className={cx(styles.navItem, styles.navList, styles.moveRow)}>
      <select
        autoFocus
        className={styles.moveSelect}
        value={group}
        onChange={e => setGroup(e.target.value)}
      >
        <option value="">No group</option>
        {sortByName(groups).map(group => (
          <option key={group.id} value={group.name}>
            {group.name}
          </option>
        ))}
      </select>

      <SaveAction title="Save" onClick={save} />
    </div>
  );
};

type SidebarNewItemRowProps = {
  kind: NewItemKind;
  act: Action;
  cancel: () => void;
};

const SidebarNewItemRow = ({ kind, act, cancel }: SidebarNewItemRowProps) => {
  const [name, setName] = useState('');

  const save = async () => {
    const trimmed = name.trim();

    if (trimmed) {
      const ok = kind === 'group'
        ? await act(API.addGroup, { group: trimmed })
        : await act(API.addList, { list: trimmed });

      if (ok) {
        setName('');
        cancel();
      }
    } else {
      cancel();
    }
  };

  return (
    <div className={cx(styles.newListInput, styles.renameRow, styles.navItem)}>
      <input
        autoFocus
        autoComplete="off"
        placeholder={kind === 'group' ? MSG.groupName : MSG.listName}
        value={name}
        onChange={e => setName(e.target.value)}
        onKeyDown={submitOnEnter(save, cancel)}
      />

      <SaveAction title="Add" onClick={save} />
    </div>
  );
};

export {
  SidebarListRow,
  SidebarNewItemRow,
};
