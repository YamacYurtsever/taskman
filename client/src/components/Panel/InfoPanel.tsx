import infoContent from '../../content/information.md?raw';
import { extractHeadings, renderMarkdown, scrollToAnchor } from '../../lib/markdown';
import styles from './InfoPanel.module.css';

const InfoPanelHeader = () => <h2 className={styles.title}>Information</h2>;

const InfoPanelBody = () => {
  const sections = extractHeadings(infoContent, 1);
  const contentNodes = renderMarkdown(infoContent, { linkClassName: styles.link });

  return (
    <>
      {sections.length > 1 && (
        <nav className={styles.nav}>
          {sections.map(section => (
            <button
              key={section.id}
              className={styles.navPill}
              onClick={() => scrollToAnchor(section.id)}
            >
              {section.label}
            </button>
          ))}
        </nav>
      )}
      <div className={styles.content}>{contentNodes}</div>
    </>
  );
};

export { InfoPanelHeader, InfoPanelBody };
