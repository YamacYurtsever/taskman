import type { PropsWithChildren, SVGProps } from 'react';

type IconProps = SVGProps<SVGSVGElement> & {
  size?: number;
};

const Icon = ({ children, size = 12, ...rest }: PropsWithChildren<IconProps>) => (
  <svg
    width={size}
    height={size}
    viewBox="0 0 16 16"
    fill="none"
    stroke="currentColor"
    strokeWidth={1.8}
    strokeLinecap="round"
    strokeLinejoin="round"
    {...rest}
  >
    {children}
  </svg>
);

const CheckIcon = (props: IconProps) => (
  <Icon {...props}>
    <path d="M3 8.5l3 3L13 5" />
  </Icon>
);

const DeleteIcon = (props: IconProps) => (
  <Icon {...props}>
    <path d="M3 3l10 10M13 3L3 13" />
  </Icon>
);

const ContinueIcon = (props: IconProps) => (
  <Icon {...props}>
    <path d="M4 4l4 4-4 4" />
    <path d="M9 4l4 4-4 4" />
  </Icon>
);

const ChevronLeftIcon = (props: IconProps) => (
  <Icon {...props}>
    <path d="M10 12L6 8l4-4" />
  </Icon>
);

const ChevronRightIcon = (props: IconProps) => (
  <Icon {...props}>
    <path d="M6 4l4 4-4 4" />
  </Icon>
);

const PlusIcon = (props: IconProps) => (
  <Icon {...props}>
    <path d="M8 3v10M3 8h10" />
  </Icon>
);

const EditIcon = (props: IconProps) => (
  <Icon {...props}>
    <path d="M12 2l2 2-9 9-3 1 1-3 9-9z" />
  </Icon>
);

const MoveIcon = (props: IconProps) => (
  <Icon {...props}>
    <path d="M3 8h10M9 4l4 4-4 4" />
  </Icon>
);

const MenuIcon = (props: IconProps) => (
  <Icon {...props}>
    <path d="M3 4h10M3 8h10M3 12h10" />
  </Icon>
);

const NoteIcon = (props: IconProps) => (
  <Icon {...props}>
    <path d="M4 2h6l4 4v8a1 1 0 01-1 1H4a1 1 0 01-1-1V3a1 1 0 011-1z" />
    <path d="M10 2v4h4" />
    <path d="M6 9h5M6 12h3" />
  </Icon>
);

export {
  CheckIcon,
  DeleteIcon,
  ContinueIcon,
  ChevronLeftIcon,
  ChevronRightIcon,
  PlusIcon,
  EditIcon,
  MoveIcon,
  MenuIcon,
  NoteIcon,
};
