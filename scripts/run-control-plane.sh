#!/usr/bin/env bash
set -euo pipefail

HINDSIGHT_SOURCE_ROOT="${HINDSIGHT_SOURCE_ROOT:-$HOME/code/vendor/hindsight}"
CONTROL_PLANE_DIR="$HINDSIGHT_SOURCE_ROOT/hindsight-control-plane"
PORT="${HINDSIGHT_CP_PORT:-${PORT:-9999}}"
HOSTNAME_BIND="${HINDSIGHT_CP_HOST:-${HOSTNAME:-127.0.0.1}}"
API_URL="${HINDSIGHT_CP_DATAPLANE_API_URL:-http://127.0.0.1:8888}"

[[ -d "$CONTROL_PLANE_DIR" ]] || { echo "missing control plane dir: $CONTROL_PLANE_DIR" >&2; exit 1; }
[[ -f "$HINDSIGHT_SOURCE_ROOT/package.json" ]] || { echo "missing upstream package.json: $HINDSIGHT_SOURCE_ROOT/package.json" >&2; exit 1; }

cd "$HINDSIGHT_SOURCE_ROOT"

if [[ ! -d node_modules || ! -x node_modules/.bin/next ]]; then
  echo "hindsight ui: installing upstream npm workspace dependencies..." >&2
  npm install
fi

if [[ ! -f "$HINDSIGHT_SOURCE_ROOT/hindsight-clients/typescript/dist/index.mjs" ]]; then
  echo "hindsight ui: building upstream TypeScript client..." >&2
  npm --workspace @vectorize-io/hindsight-client run build
fi

echo "hindsight ui: http://$HOSTNAME_BIND:$PORT -> $API_URL" >&2
exec env \
  PORT="$PORT" \
  HOSTNAME="$HOSTNAME_BIND" \
  HINDSIGHT_CP_DATAPLANE_API_URL="$API_URL" \
  npm --workspace @vectorize-io/hindsight-control-plane run dev
