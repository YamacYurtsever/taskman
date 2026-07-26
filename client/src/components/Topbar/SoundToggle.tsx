import { useState } from 'react';
import { isMuted, setMuted } from '../../lib/sound';
import { SoundOffIcon, SoundOnIcon } from '../icons';
import styles from './ThemeToggle.module.css';

const SoundToggle = () => {
  const [muted, setMutedState] = useState(isMuted);

  const toggle = () => {
    const next = !muted;
    setMuted(next);
    setMutedState(next);
  };

  return (
    <button
      className={styles.themeToggle}
      title={muted ? 'Unmute sounds' : 'Mute sounds'}
      onClick={toggle}
    >
      {muted ? <SoundOffIcon size={14} /> : <SoundOnIcon size={14} />}
    </button>
  );
};

export { SoundToggle };
