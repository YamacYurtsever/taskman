import { useEffect, useRef } from 'react';
import themeStyles from './ThemeToggle.module.css';
import styles from './AccentPicker.module.css';

type AccentPickerProps = {
  accentColor: string | null;
  onChange: (color: string | null) => void;
};

const DEFAULT_ACCENT = '#5b6cff';

const applyAccent = (color: string | null) => {
  const root = document.documentElement;
  if (color) {
    root.style.setProperty('--accent', color);
    root.style.setProperty('--accent-bg', `${color}1a`);
  } else {
    root.style.removeProperty('--accent');
    root.style.removeProperty('--accent-bg');
  }
};

const AccentPicker = ({ accentColor, onChange }: AccentPickerProps) => {
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    applyAccent(accentColor);
  }, [accentColor]);

  return (
    <button
      className={`${themeStyles.themeToggle} ${styles.button}`}
      title="Accent color (right-click to reset)"
      onClick={() => inputRef.current?.click()}
      onContextMenu={e => {
        e.preventDefault();
        onChange(null);
      }}
    >
      <span className={styles.swatch} style={{ background: accentColor ?? DEFAULT_ACCENT }} />
      <input
        ref={inputRef}
        className={styles.hiddenInput}
        type="color"
        tabIndex={-1}
        value={accentColor ?? DEFAULT_ACCENT}
        onChange={e => onChange(e.target.value)}
      />
    </button>
  );
};

export { AccentPicker };
