import { useEffect, useRef, useState } from 'react';
import type { PropsWithChildren } from 'react';
import styles from './SettingsMenu.module.css';

const SettingsMenu = ({ children }: PropsWithChildren) => {
  const [open, setOpen] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!open) return;

    const handlePointerDown = (e: PointerEvent) => {
      if (!containerRef.current?.contains(e.target as Node)) {
        setOpen(false);
      }
    };
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') setOpen(false);
    };

    document.addEventListener('pointerdown', handlePointerDown);
    document.addEventListener('keydown', handleKeyDown);
    return () => {
      document.removeEventListener('pointerdown', handlePointerDown);
      document.removeEventListener('keydown', handleKeyDown);
    };
  }, [open]);

  return (
    <div className={styles.container} ref={containerRef}>
      <div className={`${styles.pill} ${open ? styles.pillOpen : ''}`}>
        <button
          className={styles.gearBtn}
          title="Settings"
          aria-expanded={open}
          onClick={() => setOpen(o => !o)}
        >
          <span className={styles.gearIcon} />
        </button>
        <div className={`${styles.items} ${open ? styles.itemsOpen : ''}`}>
          <div className={styles.itemsInner}>{children}</div>
        </div>
      </div>
    </div>
  );
};

export { SettingsMenu };
