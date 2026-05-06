#!/usr/bin/env bash
set -euo pipefail

ROOT="${MEMPALACE_ROOT:-/media/u0/OneDrive_Backup/mempalace}"
APP="${MEMPALACE_APP:-$ROOT/app}"
VENV="${MEMPALACE_VENV:-$ROOT/venv}"
SCRIPT="${MEMPALACE_THREAD_SIGNAL_SCRIPT:-$APP/scripts/localai_chatgpt_thread_signals.py}"
ENV_FILE="${MEMPALACE_ENV_FILE:-$ROOT/mempalace.env}"
SOURCE_DIR="${MEMPALACE_THREAD_SIGNAL_SOURCE_DIR:-$ROOT/sources/chatgpt}"
LOCALAI_BASE_URL="${MEMPALACE_THREAD_SIGNAL_LOCALAI_BASE_URL:-http://snow-white-iii:8080/v1}"
LOCALAI_TOKEN_FILE="${MEMPALACE_THREAD_SIGNAL_LOCALAI_TOKEN_FILE:-$ROOT/secrets/localai_token}"
MCP_TOKEN_FILE="${MEMPALACE_THREAD_SIGNAL_MCP_TOKEN_FILE:-${MEMPALACE_HTTP_TOKEN_FILE:-$ROOT/secrets/http_token}}"
WING="${MEMPALACE_THREAD_SIGNAL_WING:-chatgpt_thread_signals}"
MODEL="${MEMPALACE_THREAD_SIGNAL_MODEL:-qwen3-vl-8b-instruct}"
UNIT_BASE="${MEMPALACE_THREAD_SIGNAL_UNIT_BASE:-mempalace-localai-chatgpt-thread-signals}"
RUN_DIR_ARG=""
LIMIT=""
PUBLISH=0
MCP_TIMEOUT="${MEMPALACE_THREAD_SIGNAL_MCP_TIMEOUT:-300}"
SCRIPT_PATH="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/$(basename "${BASH_SOURCE[0]}")"

usage() {
  cat <<'USAGE'
Usage: scripts/systemd/start_chatgpt_thread_signal_rebuild_snow_white_iii.sh [options]

Starts the thread-aware ChatGPT signal rebuild as the mempalace service user in
a bounded transient systemd unit with CPUQuota=200% and MemoryMax=16G.

Options:
  --run-dir PATH   reuse or inspect an existing run directory
  --limit N        process at most N segments
  --publish        publish reconciled signals back to MemPalace
  --model MODEL    LocalAI model to use
  --mcp-timeout N  MemPalace HTTP MCP timeout in seconds (default: 300)

The wrapper never deletes or overwrites palace data, never restarts services,
and refuses any path under /media/u0/Extreme SSD.
USAGE
}

while (($#)); do
  case "$1" in
    --run-dir)
      RUN_DIR_ARG="${2:?--run-dir requires a path}"
      shift 2
      ;;
    --limit)
      LIMIT="${2:?--limit requires a value}"
      shift 2
      ;;
    --publish)
      PUBLISH=1
      shift
      ;;
    --model)
      MODEL="${2:?--model requires a value}"
      shift 2
      ;;
    --mcp-timeout)
      MCP_TIMEOUT="${2:?--mcp-timeout requires a value}"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "unknown argument: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

host_lc="$(hostname | tr '[:upper:]' '[:lower:]')"
if [[ "$host_lc" != "snow-white-iii" && "$host_lc" != "snow-white-iii.local" && "${MEMPALACE_INSTALL_ALLOW_OTHER_HOST:-}" != "1" ]]; then
  echo "refusing rebuild start on host '$(hostname)'; expected snow-white-iii" >&2
  exit 2
fi

refuse_extreme_ssd() {
  case "$1" in
    /media/u0/Extreme\ SSD|/media/u0/Extreme\ SSD/*)
      echo "refusing to use /media/u0/Extreme SSD: $1" >&2
      exit 2
      ;;
  esac
}

STAMP="${MEMPALACE_THREAD_SIGNAL_STAMP:-$(date -u +%Y%m%d%H%M%S)}"
DEFAULT_RUN_DIR="$ROOT/data/localai_chatgpt_thread_signals/${STAMP}_thread_signal_rebuild"
RUN_DIR="${MEMPALACE_THREAD_SIGNAL_RUN_DIR:-${RUN_DIR_ARG:-$DEFAULT_RUN_DIR}}"
UNIT="${MEMPALACE_THREAD_SIGNAL_UNIT:-${UNIT_BASE}-${STAMP}}"

for path in "$ROOT" "$APP" "$VENV" "$SCRIPT" "$ENV_FILE" "$SOURCE_DIR" "$RUN_DIR" "$LOCALAI_TOKEN_FILE" "$MCP_TOKEN_FILE"; do
  refuse_extreme_ssd "$path"
done

if [[ "$EUID" -ne 0 ]]; then
  exec sudo env \
    MEMPALACE_ROOT="$ROOT" \
    MEMPALACE_APP="$APP" \
    MEMPALACE_VENV="$VENV" \
    MEMPALACE_THREAD_SIGNAL_SCRIPT="$SCRIPT" \
    MEMPALACE_ENV_FILE="$ENV_FILE" \
    MEMPALACE_THREAD_SIGNAL_SOURCE_DIR="$SOURCE_DIR" \
    MEMPALACE_THREAD_SIGNAL_LOCALAI_BASE_URL="$LOCALAI_BASE_URL" \
    MEMPALACE_THREAD_SIGNAL_LOCALAI_TOKEN_FILE="$LOCALAI_TOKEN_FILE" \
    MEMPALACE_THREAD_SIGNAL_MCP_TOKEN_FILE="$MCP_TOKEN_FILE" \
    MEMPALACE_THREAD_SIGNAL_WING="$WING" \
    MEMPALACE_THREAD_SIGNAL_MODEL="$MODEL" \
    MEMPALACE_THREAD_SIGNAL_UNIT_BASE="$UNIT_BASE" \
    MEMPALACE_THREAD_SIGNAL_STAMP="$STAMP" \
    MEMPALACE_THREAD_SIGNAL_RUN_DIR="$RUN_DIR" \
    MEMPALACE_THREAD_SIGNAL_UNIT="$UNIT" \
    MEMPALACE_THREAD_SIGNAL_LIMIT="$LIMIT" \
    MEMPALACE_THREAD_SIGNAL_PUBLISH="$PUBLISH" \
    MEMPALACE_THREAD_SIGNAL_MCP_TIMEOUT="$MCP_TIMEOUT" \
    "$SCRIPT_PATH"
fi

if [[ -f "$ENV_FILE" ]]; then
  set -a
  # shellcheck disable=SC1090
  . "$ENV_FILE"
  set +a
fi

HTTP_URL="${MEMPALACE_HTTP_URL:-http://${MEMPALACE_HTTP_HOST:-100.112.179.49}:${MEMPALACE_HTTP_PORT:-8765}}"

if [[ ! -f "$SCRIPT" ]]; then
  echo "missing thread signal script: $SCRIPT" >&2
  exit 1
fi
if [[ ! -x "$VENV/bin/python" ]]; then
  echo "missing MemPalace venv python: $VENV/bin/python" >&2
  exit 1
fi
if [[ ! -d "$SOURCE_DIR" ]]; then
  echo "missing ChatGPT source directory: $SOURCE_DIR" >&2
  exit 1
fi
if [[ ! -f "$LOCALAI_TOKEN_FILE" ]]; then
  echo "missing LocalAI token file: $LOCALAI_TOKEN_FILE" >&2
  exit 1
fi
if [[ ! -f "$MCP_TOKEN_FILE" ]]; then
  echo "missing MemPalace HTTP token file: $MCP_TOKEN_FILE" >&2
  exit 1
fi

LIMIT="${MEMPALACE_THREAD_SIGNAL_LIMIT:-$LIMIT}"
PUBLISH="${MEMPALACE_THREAD_SIGNAL_PUBLISH:-$PUBLISH}"
MCP_TIMEOUT="${MEMPALACE_THREAD_SIGNAL_MCP_TIMEOUT:-$MCP_TIMEOUT}"

if [[ ! "$MCP_TIMEOUT" =~ ^[0-9]+([.][0-9]+)?$ ]]; then
  echo "invalid --mcp-timeout value: $MCP_TIMEOUT" >&2
  exit 2
fi

install -d -o mempalace -g mempalace -m 0750 "$RUN_DIR"

cmd=(
  "$VENV/bin/python"
  "$SCRIPT"
  --source-dir "$SOURCE_DIR"
  --run-dir "$RUN_DIR"
  --localai-base-url "$LOCALAI_BASE_URL"
  --localai-token-file "$LOCALAI_TOKEN_FILE"
  --mempalace-url "$HTTP_URL"
  --mempalace-token-file "$MCP_TOKEN_FILE"
  --mempalace-timeout "$MCP_TIMEOUT"
  --wing "$WING"
  --model "$MODEL"
)
if [[ "$PUBLISH" -eq 1 ]]; then
  cmd+=(--publish)
fi
if [[ -n "$LIMIT" ]]; then
  if [[ ! "$LIMIT" =~ ^[0-9]+$ ]]; then
    echo "invalid --limit value: $LIMIT" >&2
    exit 2
  fi
  cmd+=(--limit "$LIMIT")
fi

systemd-run \
  --unit="$UNIT" \
  --description="MemPalace thread-aware ChatGPT signal rebuild" \
  --collect \
  --property=User=mempalace \
  --property=Group=mempalace \
  --property=WorkingDirectory="$APP" \
  --property=NoNewPrivileges=true \
  --property=ProtectSystem=strict \
  --property=ReadWritePaths="$ROOT" \
  --property=MemoryMax=16G \
  --property=CPUQuota=200% \
  --property=Nice=10 \
  --property=IOSchedulingClass=best-effort \
  --property=IOSchedulingPriority=7 \
  --setenv=PYTHONPATH="$APP" \
  --setenv=MEMPALACE_ROOT="$ROOT" \
  --setenv=MEMPALACE_APP="$APP" \
  --setenv=MEMPALACE_VENV="$VENV" \
  --setenv=MEMPALACE_HTTP_URL="$HTTP_URL" \
  --setenv=LOCALAI_BASE_URL="$LOCALAI_BASE_URL" \
  --setenv=LOCALAI_TOKEN_FILE="$LOCALAI_TOKEN_FILE" \
  --setenv=MEMPALACE_HTTP_TOKEN_FILE="$MCP_TOKEN_FILE" \
  --setenv=LOCALAI_THREAD_SIGNAL_WING="$WING" \
  --setenv=LOCALAI_THREAD_SIGNAL_MODEL="$MODEL" \
  --setenv=LOCALAI_THREAD_SIGNAL_RUN_DIR="$RUN_DIR" \
  "${cmd[@]}"

cat <<EOF
Thread-aware ChatGPT signal rebuild submitted.

Unit:      $UNIT
Run dir:   $RUN_DIR
Progress:  $RUN_DIR/progress.json
Checkpoint: $RUN_DIR/segment_checkpoint.jsonl
Artifacts: $RUN_DIR/segment_extractions.jsonl
           $RUN_DIR/invalid_outputs.jsonl
           $RUN_DIR/reconciled_signals.jsonl
Publish:   $RUN_DIR/publish_checkpoint.jsonl (only if --publish is used)
MCP timeout: $MCP_TIMEOUT seconds
Journal:   journalctl -fu $UNIT
EOF
