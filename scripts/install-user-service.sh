#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
UNIT_DIR="$HOME/.config/systemd/user"
UNIT_SRC="$ROOT/systemd/user/hindsight-api.service"
UNIT_DST="$UNIT_DIR/hindsight-api.service"

mkdir -p "$UNIT_DIR"
cp "$UNIT_SRC" "$UNIT_DST"
systemctl --user daemon-reload

echo "installed $UNIT_DST"
echo "start:   systemctl --user start hindsight-api"
echo "status:  systemctl --user status hindsight-api --no-pager"
echo "logs:    journalctl --user -u hindsight-api -f"
