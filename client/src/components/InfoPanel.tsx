import infoContent from '../content/information.md?raw';
import { renderMarkdown } from '../lib/markdown';
import styles from './InfoPanel.module.css';

const InfoPanelHeader = () => <h2 className={styles.title}>Information</h2>;

const InfoPanelBody = () => {
  const contentNodes = renderMarkdown(infoContent, { linkClassName: styles.link });
  return <div className={styles.content}>{contentNodes}</div>;
};

export { InfoPanelHeader, InfoPanelBody };
