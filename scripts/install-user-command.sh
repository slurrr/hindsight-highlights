#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TARGET_DIR="$HOME/.local/bin"
TARGET="$TARGET_DIR/hindsight"

mkdir -p "$TARGET_DIR"
ln -sfn "$ROOT/scripts/hindsight" "$TARGET"

echo "installed $TARGET -> $ROOT/scripts/hindsight"
