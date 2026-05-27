#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_FILE="${HINDSIGHT_ENV_FILE:-$ROOT/env/hindsight.env}"

cd "$ROOT"
mkdir -p "$HOME/runs/hindsight"

if [[ ! -d "$ROOT/.venv" ]]; then
  echo "missing .venv; run: uv sync" >&2
  exit 1
fi

if [[ ! -f "$ENV_FILE" ]]; then
  echo "missing env file: $ENV_FILE" >&2
  exit 1
fi

set -a
# shellcheck disable=SC1090
source "$ENV_FILE"
if [[ -f "$ROOT/env/hindsight.local.env" ]]; then
  # Optional ignored local overrides/secrets.
  # shellcheck disable=SC1091
  source "$ROOT/env/hindsight.local.env"
fi
set +a

exec "$ROOT/.venv/bin/hindsight-api" \
  --host "${HINDSIGHT_API_HOST:-127.0.0.1}" \
  --port "${HINDSIGHT_API_PORT:-8888}" \
  "$@"
