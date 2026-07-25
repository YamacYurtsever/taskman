const MUTED_KEY = 'soundMuted';

const isMuted = () => localStorage.getItem(MUTED_KEY) === 'true';

const setMuted = (muted: boolean) => {
  localStorage.setItem(MUTED_KEY, String(muted));
};

const playFile = (path: string) => {
  if (isMuted()) return;
  new Audio(path).play().catch(() => {
    // audio unavailable (unsupported browser, blocked autoplay, etc.) — fail silently
  });
};

export const playDoneSound = () => playFile('/sounds/completed.mp3');

export const playContinueSound = () => playFile('/sounds/continued.mp3');

export { isMuted, setMuted };
