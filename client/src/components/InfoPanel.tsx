import infoContent from '../content/information.md?raw';
import { renderMarkdown } from '../lib/markdown';
import styles from './InfoPanel.module.css';
import { Panel } from './Panel';
import type { PanelSize } from './Panel';

type InfoPanelProps = {
  onClose: () => void;
  panelSize?: PanelSize;
  onResize?: (size: PanelSize) => void;
  resizable?: boolean;
};

const InfoPanel = ({ onClose, panelSize, onResize, resizable }: InfoPanelProps) => {
  const contentNodes = renderMarkdown(infoContent, { linkClassName: styles.link });

  return (
    <Panel
      onClose={onClose}
      panelSize={panelSize}
      onResize={onResize}
      resizable={resizable}
      header={<h2 className={styles.title}>Information</h2>}
    >
      <div className={styles.content}>{contentNodes}</div>
    </Panel>
  );
};

export { InfoPanel };
