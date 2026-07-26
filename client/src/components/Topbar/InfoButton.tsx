import { InfoIcon } from '../icons';
import themeStyles from './ThemeToggle.module.css';

type InfoButtonProps = {
  onClick: () => void;
};

const InfoButton = ({ onClick }: InfoButtonProps) => (
  <button className={themeStyles.themeToggle} title="Information" onClick={onClick}>
    <InfoIcon />
  </button>
);

export { InfoButton };
