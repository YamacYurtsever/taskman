import type { ReactNode } from 'react';

const CHECKBOX_LINE = /^(\s*)-\s\[([ xX])\]\s(.*)$/;

const checkboxProgress = (text: string): { done: number; total: number } | null => {
  let done = 0;
  let total = 0;

  for (const line of text.split('\n')) {
    const match = line.match(CHECKBOX_LINE);
    if (!match) continue;
    total += 1;
    if (match[2].toLowerCase() === 'x') done += 1;
  }

  return total > 0 ? { done, total } : null;
};

const renderLineWithLinks = (line: string, lineIdx: number, linkClassName?: string): ReactNode[] => {
  const urlRegex = /https?:\/\/[^\s]+/g;
  let lastIndex = 0;
  let match: RegExpExecArray | null;
  const lineNodes: ReactNode[] = [];

  while ((match = urlRegex.exec(line)) !== null) {
    if (match.index > lastIndex) {
      lineNodes.push(line.slice(lastIndex, match.index));
    }
    lineNodes.push(
      <a
        key={`${lineIdx}-${match.index}`}
        href={match[0]}
        target="_blank"
        rel="noopener noreferrer"
        className={linkClassName}
        onClick={e => e.stopPropagation()}
      >
        {match[0]}
      </a>,
    );
    lastIndex = match.index + match[0].length;
  }

  if (lastIndex < line.length) lineNodes.push(line.slice(lastIndex));
  return lineNodes.length > 0 ? lineNodes : [line];
};

type RenderMarkdownOptions = {
  linkClassName?: string;
  checkboxLineClassName?: string;
  onToggleCheckbox?: (lineIdx: number) => void;
};

const renderMarkdown = (text: string, options: RenderMarkdownOptions = {}): ReactNode[] => {
  const { linkClassName, checkboxLineClassName, onToggleCheckbox } = options;
  const nodes: ReactNode[] = [];

  text.split('\n').forEach((line, lineIdx) => {
    if (lineIdx > 0) nodes.push(<br key={`br-${lineIdx}`} />);

    const checkboxMatch = line.match(CHECKBOX_LINE);
    if (checkboxMatch) {
      const [, indent, mark, rest] = checkboxMatch;
      nodes.push(
        <label
          key={`line-${lineIdx}`}
          className={checkboxLineClassName}
          style={indent ? { marginLeft: `${indent.length * 0.6}em` } : undefined}
        >
          <input
            type="checkbox"
            checked={mark.toLowerCase() === 'x'}
            onChange={() => onToggleCheckbox?.(lineIdx)}
            onClick={e => e.stopPropagation()}
          />
          {renderLineWithLinks(rest, lineIdx, linkClassName)}
        </label>,
      );
      return;
    }

    nodes.push(...renderLineWithLinks(line, lineIdx, linkClassName));
  });

  return nodes;
};

export { CHECKBOX_LINE, checkboxProgress, renderMarkdown };
