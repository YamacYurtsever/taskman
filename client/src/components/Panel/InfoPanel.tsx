import infoContent from '../../content/information.md?raw';
import { MarkdownSections } from './MarkdownSections';
import styles from './InfoPanel.module.css';

const InfoPanelHeader = () => <h2 className={styles.title}>Information</h2>;

const InfoPanelBody = () => (
  <MarkdownSections text={infoContent} contentClassName={styles.content} linkClassName={styles.link} />
);

export { InfoPanelHeader, InfoPanelBody };
