import { useEffect } from 'react';
import styles from './AccentPicker.module.css';

type AccentPickerProps = {
  accentColor: string | null;
  onChange: (color: string) => void;
};

const DEFAULT_ACCENT = '#5b6cff';

const applyAccent = (color: string) => {
  const root = document.documentElement;
  root.style.setProperty('--accent', color);
  root.style.setProperty('--accent-bg', `${color}1a`);
};

const AccentPicker = ({ accentColor, onChange }: AccentPickerProps) => {
  useEffect(() => {
    if (accentColor) applyAccent(accentColor);
  }, [accentColor]);

  return (
    <input
      className={styles.accentPicker}
      type="color"
      title="Accent color"
      value={accentColor ?? DEFAULT_ACCENT}
      onChange={e => onChange(e.target.value)}
    />
  );
};

export { AccentPicker };
