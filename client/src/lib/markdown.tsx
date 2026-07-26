import type { MouseEvent, ReactNode } from 'react';

const CHECKBOX_LINE = /^(\s*)-\s\[([ xX])\]\s(.*)$/;
const HEADER_LINE = /^(#{1,3})\s+(.*)$/;
const LINK_TOKEN = /\[([^\]]+)\]\(([^)]+)\)|https?:\/\/[^\s]+/g;
const HEADING_TAGS = ['h2', 'h3', 'h4'] as const;

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

const slugify = (text: string) =>
  text.trim().toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-+|-+$/g, '');

const scrollToAnchor = (id: string) => {
  document.getElementById(id)?.scrollIntoView({ behavior: 'smooth', block: 'start' });
};

const renderLineWithLinks = (line: string, lineIdx: number, linkClassName?: string): ReactNode[] => {
  LINK_TOKEN.lastIndex = 0;
  let lastIndex = 0;
  let match: RegExpExecArray | null;
  const lineNodes: ReactNode[] = [];

  while ((match = LINK_TOKEN.exec(line)) !== null) {
    if (match.index > lastIndex) {
      lineNodes.push(line.slice(lastIndex, match.index));
    }

    const isReference = match[1] !== undefined;
    const label = isReference ? match[1] : match[0];
    const target = isReference ? match[2] : match[0];
    const isAnchor = target.startsWith('#');

    lineNodes.push(
      <a
        key={`${lineIdx}-${match.index}`}
        href={target}
        className={linkClassName}
        target={isAnchor ? undefined : '_blank'}
        rel={isAnchor ? undefined : 'noopener noreferrer'}
        onClick={(e: MouseEvent) => {
          e.stopPropagation();
          if (!isAnchor) return;
          e.preventDefault();
          scrollToAnchor(target.slice(1));
        }}
      >
        {label}
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
  let prevWasHeader = false;

  text.split('\n').forEach((line, lineIdx) => {
    // Headings already carry their own block-level break + bottom margin, so the
    // line right after one shouldn't also get a manual <br> — but this needs to
    // apply uniformly (including when that next line is itself another heading),
    // otherwise a blank line between two headings loses its only source of gap.
    if (lineIdx > 0 && !prevWasHeader) nodes.push(<br key={`br-${lineIdx}`} />);

    const headerMatch = line.match(HEADER_LINE);
    if (headerMatch) {
      const [, hashes, headerText] = headerMatch;
      const Tag = HEADING_TAGS[hashes.length - 1];
      nodes.push(
        <Tag key={`line-${lineIdx}`} id={slugify(headerText)}>
          {renderLineWithLinks(headerText, lineIdx, linkClassName)}
        </Tag>,
      );
      prevWasHeader = true;
      return;
    }

    prevWasHeader = false;

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
