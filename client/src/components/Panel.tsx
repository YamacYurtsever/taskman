import { useEffect, useRef } from 'react';
import type { CSSProperties, ReactNode } from 'react';
import { cx } from '../lib/utils';
import styles from './Panel.module.css';

export type PanelSize = number | 'full' | null;

type PanelProps = {
  closing?: boolean;
  onClose: () => void;
  panelSize?: PanelSize;
  onResize?: (size: PanelSize) => void;
  resizable?: boolean;
  header?: ReactNode;
  children: ReactNode;
};

const MIN_PANEL_W = 360;
const FULL_SNAP_RATIO = 0.85;
// Guarantees at least one card column (--card-max-w) plus its padding stays visible
// before the panel is allowed to snap to full-width, regardless of the ratio above.
const MIN_CONTENT_W = 320;

const Panel = ({
  closing = false,
  onClose,
  panelSize = null,
  onResize,
  resizable = false,
  header,
  children,
}: PanelProps) => {
  const panelRef = useRef<HTMLDivElement>(null);
  const dragAbortRef = useRef<AbortController | null>(null);

  useEffect(() => {
    return () => dragAbortRef.current?.abort();
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

  const handlePointerDown = (e: React.PointerEvent) => {
    const rect = panelRef.current?.getBoundingClientRect();
    const containerRect = panelRef.current?.parentElement?.getBoundingClientRect();
    if (!rect || !containerRect || !onResize) return;

    const startX = e.clientX;
    const startWidth = rect.width;
    const fullThreshold = Math.min(
      containerRect.width * FULL_SNAP_RATIO,
      containerRect.width - MIN_CONTENT_W,
    );

    dragAbortRef.current?.abort();
    const controller = new AbortController();
    dragAbortRef.current = controller;
    document.body.style.userSelect = 'none';

    window.addEventListener('pointermove', (moveEvent: PointerEvent) => {
      const rawWidth = startWidth + (startX - moveEvent.clientX);
      onResize(rawWidth >= fullThreshold ? 'full' : Math.max(MIN_PANEL_W, rawWidth));
    }, { signal: controller.signal });

    window.addEventListener('pointerup', () => {
      document.body.style.userSelect = '';
      controller.abort();
    }, { signal: controller.signal });
  };

  const panelStyle: CSSProperties | undefined = !resizable
    ? undefined
    : panelSize === 'full'
      ? { width: '100%', borderLeft: 'none' }
      : typeof panelSize === 'number'
        ? { width: `${panelSize}px` }
        : undefined;

  return (
    <div className={cx(styles.panel, closing && styles.closing)} style={panelStyle} ref={panelRef}>
      {resizable && (
        <div className={styles.resizeHandle} onPointerDown={handlePointerDown} />
      )}
      <div className={styles.header}>
        {header}
        <button className={styles.closeBtn} onClick={onClose} title="Close (Esc)">✕</button>
      </div>
      {children}
    </div>
  );
};

export { Panel };
