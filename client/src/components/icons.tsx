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

const DuplicateIcon = (props: IconProps) => (
  <Icon {...props}>
    <rect x="5" y="5" width="8" height="8" rx="1.5" />
    <path d="M3 10V4.5A1.5 1.5 0 014.5 3H10" />
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

const PinIcon = (props: IconProps) => (
  <Icon fill="currentColor" stroke="none" opacity={0.5} {...props}>
    <path
      fillRule="evenodd"
      d="M4.25 3A1.25 1.25 0 0 1 5.5 1.75h5A1.25 1.25 0 0 1 11.75 3v.45a1.25 1.25 0 0 1-.48.98L10.2 5.27v1.1l1.93 1.93a.75.75 0 0 1-.33 1.26l-3.05.76v3.93a.75.75 0 0 1-1.5 0v-3.93l-3.05-.76a.75.75 0 0 1-.33-1.26L5.8 6.37v-1.1L4.73 4.43a1.25 1.25 0 0 1-.48-.98z"
    />
  </Icon>
);

const PinFilledIcon = (props: IconProps) => (
  <Icon fill="currentColor" stroke="none" {...props}>
    <path
      fillRule="evenodd"
      d="M4.25 3A1.25 1.25 0 0 1 5.5 1.75h5A1.25 1.25 0 0 1 11.75 3v.45a1.25 1.25 0 0 1-.48.98L10.2 5.27v1.1l1.93 1.93a.75.75 0 0 1-.33 1.26l-3.05.76v3.93a.75.75 0 0 1-1.5 0v-3.93l-3.05-.76a.75.75 0 0 1-.33-1.26L5.8 6.37v-1.1L4.73 4.43a1.25 1.25 0 0 1-.48-.98z"
    />
  </Icon>
);

const SignOutIcon = (props: IconProps) => (
  <Icon {...props}>
    <path d="M6 3H4a1 1 0 00-1 1v8a1 1 0 001 1h2" />
    <path d="M10 11l3-3-3-3" />
    <path d="M6 8h7" />
  </Icon>
);

type GoogleLogoProps = { size?: number };

const GoogleLogoIcon = ({ size = 18 }: GoogleLogoProps) => (
  <svg width={size} height={size} viewBox="0 0 18 18" xmlns="http://www.w3.org/2000/svg">
    <path d="M17.64 9.2c0-.637-.057-1.251-.164-1.84H9v3.481h4.844c-.209 1.125-.843 2.078-1.796 2.716v2.259h2.908c1.702-1.567 2.684-3.875 2.684-6.615z" fill="#4285F4"/>
    <path d="M9 18c2.43 0 4.467-.806 5.956-2.184l-2.908-2.259c-.806.54-1.837.86-3.048.86-2.344 0-4.328-1.584-5.036-3.711H.957v2.332A8.997 8.997 0 009 18z" fill="#34A853"/>
    <path d="M3.964 10.706A5.41 5.41 0 013.682 9c0-.593.102-1.17.282-1.706V4.962H.957A8.996 8.996 0 000 9c0 1.452.348 2.827.957 4.038l3.007-2.332z" fill="#FBBC05"/>
    <path d="M9 3.58c1.321 0 2.508.454 3.44 1.345l2.582-2.58C13.463.891 11.426 0 9 0A8.997 8.997 0 00.957 4.962L3.964 7.294C4.672 5.163 6.656 3.58 9 3.58z" fill="#EA4335"/>
  </svg>
);

export {
  CheckIcon,
  DeleteIcon,
  ContinueIcon,
  ChevronLeftIcon,
  ChevronRightIcon,
  PlusIcon,
  EditIcon,
  DuplicateIcon,
  MoveIcon,
  MenuIcon,
  NoteIcon,
  PinIcon,
  PinFilledIcon,
  SignOutIcon,
  GoogleLogoIcon,
};
