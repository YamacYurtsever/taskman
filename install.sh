#!/bin/zsh
SHELL_FILE="$(cd "$(dirname "$0")" && pwd)/shell/taskman.sh"
MARKER="# taskman shell functions"
ZSHRC="$HOME/.zshrc"

if grep -qF "$MARKER" "$ZSHRC" 2>/dev/null; then
  echo "taskman: shell functions already installed in $ZSHRC"
  exit 0
fi

echo "" >> "$ZSHRC"
echo "$MARKER" >> "$ZSHRC"
echo "source \"$SHELL_FILE\"" >> "$ZSHRC"
echo "taskman: added shell functions to $ZSHRC"
echo "taskman: run 'source ~/.zshrc' to activate"
