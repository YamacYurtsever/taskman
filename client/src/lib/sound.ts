const playFile = (path: string) => {
  new Audio(path).play().catch(() => {
    // audio unavailable (unsupported browser, blocked autoplay, etc.) — fail silently
  });
};

export const playDoneSound = () => playFile('/sounds/completed.mp3');

export const playContinueSound = () => playFile('/sounds/continued.mp3');
