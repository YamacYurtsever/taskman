import { useEffect, useState } from 'react';
import styles from './ThemeToggle.module.css';

type Theme = 'light' | 'dark';

const getInitialTheme = (): Theme => {
  const saved = localStorage.getItem('theme') as Theme | null;
  return saved ?? 'light';
};

const ThemeToggle = () => {
  const [theme, setTheme] = useState<Theme>(getInitialTheme);

  useEffect(() => {
    const root = document.documentElement;
    root.setAttribute('data-theme', theme);
    localStorage.setItem('theme', theme);
  }, [theme]);

  const toggle = () =>
    setTheme(t => (t === 'dark' ? 'light' : 'dark'));

  return (
    <button
      className={styles.themeToggle}
      title="Toggle theme"
      onClick={toggle}
    >
      {theme === 'dark' ? '☀' : '☾'}
    </button>
  );
};

export { ThemeToggle };
