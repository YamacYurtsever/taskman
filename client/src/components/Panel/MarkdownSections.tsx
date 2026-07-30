import type { HTMLAttributes } from 'react';
import { extractHeadings, renderMarkdown, scrollToAnchor } from '../../lib/markdown';
import type { RenderMarkdownOptions } from '../../lib/markdown';
import styles from './Panel.module.css';

type MarkdownSectionsProps = RenderMarkdownOptions & {
  text: string;
  contentClassName: string;
  contentProps?: HTMLAttributes<HTMLDivElement>;
};

// Shared by every place that renders markdown text inside a Panel (task
// descriptions, the info panel) so top-level headers always generate the same
// nav-pill row, instead of each caller deciding for itself whether to.
const MarkdownSections = ({ text, contentClassName, contentProps, ...options }: MarkdownSectionsProps) => {
  const sections = extractHeadings(text, 1);
  const contentNodes = renderMarkdown(text, options);

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
      <div className={contentClassName} {...contentProps}>
        {contentNodes}
      </div>
    </>
  );
};

export { MarkdownSections };
