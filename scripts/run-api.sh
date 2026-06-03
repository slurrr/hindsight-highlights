#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SERVICE_ENV_FILE="${HINDSIGHT_ENV_FILE:-$ROOT/env/hindsight.env}"
LAUNCH_ENV_FILE="${HINDSIGHT_LAUNCH_ENV_FILE:-$ROOT/env/hindsight.launch.env}"
LOCAL_ENV_FILE="$ROOT/env/hindsight.local.env"
RUN_ROOT="${HINDSIGHT_RUN_ROOT:-$HOME/runs/hindsight-highlights}"

load_env_file() {
  local file="$1"
  if [[ -f "$file" ]]; then
    set -a
    # shellcheck disable=SC1090
    source "$file"
    set +a
  fi
}

wait_for_http() {
  local url="$1"
  local timeout_seconds="$2"
  local interval_seconds="$3"
  local deadline=$((SECONDS + timeout_seconds))

  while (( SECONDS < deadline )); do
    if curl -fsS "$url" >/dev/null 2>&1; then
      return 0
    fi
    sleep "$interval_seconds"
  done

  echo "timed out waiting for $url after ${timeout_seconds}s" >&2
  return 1
}

start_background_command() {
  local command_text="$1"
  local log_file="$2"
  mkdir -p "$(dirname "$log_file")"
  nohup /usr/bin/bash -lc "$command_text" >"$log_file" 2>&1 </dev/null &
  echo $!
}

if [[ ! -d "$ROOT/.venv" ]]; then
  echo "missing .venv; run: uv sync" >&2
  exit 1
fi

if [[ ! -f "$SERVICE_ENV_FILE" ]]; then
  echo "missing env file: $SERVICE_ENV_FILE" >&2
  exit 1
fi

load_env_file "$SERVICE_ENV_FILE"
load_env_file "$LAUNCH_ENV_FILE"
load_env_file "$LOCAL_ENV_FILE"

LLM_MODEL="${HINDSIGHT_LLM_MODEL:-${HINDSIGHT_API_LLM_MODEL:-}}"
LLM_STACK="${HINDSIGHT_LLM_STACK:-}"
LLM_BASE_URL="${HINDSIGHT_LLM_BASE_URL:-${HINDSIGHT_API_LLM_BASE_URL:-}}"
LLM_START_CMD="${HINDSIGHT_LLM_START_CMD:-}"
LLM_HEALTH_URL="${HINDSIGHT_LLM_HEALTH_URL:-}"
LLM_START_TIMEOUT="${HINDSIGHT_LLM_START_TIMEOUT:-600}"
LLM_START_INTERVAL="${HINDSIGHT_LLM_START_INTERVAL:-2}"
LLM_SKIP_START="${HINDSIGHT_LLM_SKIP_START:-0}"
WAIT_FOR_LLM="${HINDSIGHT_LLM_WAIT_FOR_HEALTH:-1}"

FORWARD_ARGS=()
while (($#)); do
  case "$1" in
    --llm-model)
      LLM_MODEL="${2:?missing value for --llm-model}"
      shift 2
      ;;
    --llm-stack)
      LLM_STACK="${2:?missing value for --llm-stack}"
      shift 2
      ;;
    --llm-base-url)
      LLM_BASE_URL="${2:?missing value for --llm-base-url}"
      shift 2
      ;;
    --llm-start-cmd)
      LLM_START_CMD="${2:?missing value for --llm-start-cmd}"
      shift 2
      ;;
    --llm-health-url)
      LLM_HEALTH_URL="${2:?missing value for --llm-health-url}"
      shift 2
      ;;
    --llm-start-timeout)
      LLM_START_TIMEOUT="${2:?missing value for --llm-start-timeout}"
      shift 2
      ;;
    --llm-start-interval)
      LLM_START_INTERVAL="${2:?missing value for --llm-start-interval}"
      shift 2
      ;;
    --skip-llm-start)
      LLM_SKIP_START=1
      shift
      ;;
    --no-wait-for-llm)
      WAIT_FOR_LLM=0
      shift
      ;;
    --wait-for-llm)
      WAIT_FOR_LLM=1
      shift
      ;;
    --)
      shift
      FORWARD_ARGS+=("$@")
      break
      ;;
    *)
      FORWARD_ARGS+=("$1")
      shift
      ;;
  esac
done

# Hindsight service config provides the main LLM settings. Launch-time
# LLM variables are only needed when the wrapper is also starting vLLM.

if [[ -n "$LLM_MODEL" ]]; then
  export HINDSIGHT_API_LLM_MODEL="$LLM_MODEL"
fi
if [[ -n "$LLM_BASE_URL" ]]; then
  export HINDSIGHT_API_LLM_BASE_URL="$LLM_BASE_URL"
fi
if [[ -n "$LLM_MODEL" ]]; then
  export HINDSIGHT_LLM_MODEL="$LLM_MODEL"
fi
if [[ -n "$LLM_STACK" ]]; then
  export HINDSIGHT_LLM_STACK="$LLM_STACK"
fi
if [[ -n "$LLM_BASE_URL" ]]; then
  export HINDSIGHT_LLM_BASE_URL="$LLM_BASE_URL"
fi

mkdir -p "$RUN_ROOT/logs"

if [[ "$LLM_SKIP_START" -eq 1 ]]; then
  :
elif [[ -n "$LLM_START_CMD" ]]; then
  llm_ready=0
  if [[ -n "$LLM_HEALTH_URL" ]] && curl -fsS "$LLM_HEALTH_URL" >/dev/null 2>&1; then
    llm_ready=1
  fi

  if [[ "$llm_ready" -eq 0 ]]; then
    stamp="$(date -u +%Y%m%dT%H%M%SZ)"
    llm_log="$RUN_ROOT/logs/llm-${stamp}.log"
    echo "starting LLM via launcher command" >&2
    echo "LLM log: $llm_log" >&2
    start_background_command "$LLM_START_CMD" "$llm_log" >/dev/null
    if [[ "$WAIT_FOR_LLM" -eq 1 && -n "$LLM_HEALTH_URL" ]]; then
      wait_for_http "$LLM_HEALTH_URL" "$LLM_START_TIMEOUT" "$LLM_START_INTERVAL"
    fi
  fi
fi

exec "$ROOT/.venv/bin/hindsight-api" "${FORWARD_ARGS[@]}"
