#!/usr/bin/env bash
set -euo pipefail

ROOT="${MEMPALACE_ROOT:-/media/u0/OneDrive_Backup/mempalace}"
APP="${MEMPALACE_APP:-$ROOT/app}"
VENV="${MEMPALACE_VENV:-$ROOT/venv}"
ENV_FILE="${MEMPALACE_ENV_FILE:-$ROOT/mempalace.env}"
RUN_DIR="${MEMPALACE_ONTOLOGY_RUN_ROOT:-$ROOT/data/ontology}"
SOURCE_WING="${MEMPALACE_ONTOLOGY_SOURCE_WING:-chatgpt_signals}"
LOCALAI_BASE_URL="${MEMPALACE_ONTOLOGY_LOCALAI_BASE_URL:-http://snow-white-iii:8080/v1}"
LOCALAI_TOKEN_FILE="${MEMPALACE_ONTOLOGY_LOCALAI_TOKEN_FILE:-$ROOT/secrets/localai_token}"
LOCALAI_MODEL="${MEMPALACE_ONTOLOGY_LOCALAI_MODEL:-qwen3-vl-8b-instruct}"
MCP_TOKEN_FILE="${MEMPALACE_ONTOLOGY_MCP_TOKEN_FILE:-${MEMPALACE_HTTP_TOKEN_FILE:-$ROOT/secrets/http_token}}"
UNIT="${MEMPALACE_ONTOLOGY_UNIT:-mempalace-ontology-chatgpt-signals}"
APPLY_COPIES=0

usage() {
  cat <<'USAGE'
Usage: scripts/systemd/start_ontology_runner_snow_white_iii.sh [options]

Starts the ChatGPT signal ontology runner as the mempalace service user in a
transient systemd service with CPUQuota=200% and MemoryMax=16G.

Options:
  --unit NAME          systemd unit name
  --run-dir PATH      ontology run root
  --source-wing WING  source wing to read, default chatgpt_signals
  --apply-copies      opt in to materializing accepted ontology copies

Default behavior writes progressive ontology artifacts and an apply-ready
manifest only. It does not copy drawers unless --apply-copies is present.
USAGE
}

while (($#)); do
  case "$1" in
    --unit)
      UNIT="${2:?--unit requires a unit name}"
      shift 2
      ;;
    --run-dir)
      RUN_DIR="${2:?--run-dir requires a path}"
      shift 2
      ;;
    --source-wing)
      SOURCE_WING="${2:?--source-wing requires a wing}"
      shift 2
      ;;
    --apply-copies)
      APPLY_COPIES=1
      shift
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
  echo "refusing runner start on host '$(hostname)'; expected snow-white-iii" >&2
  exit 2
fi

for path in "$ROOT" "$APP" "$VENV" "$RUN_DIR" "$LOCALAI_TOKEN_FILE" "$MCP_TOKEN_FILE"; do
  case "$path" in
    /media/u0/Extreme\ SSD|/media/u0/Extreme\ SSD/*)
      echo "refusing to use /media/u0/Extreme SSD: $path" >&2
      exit 2
      ;;
  esac
done

if [[ "$EUID" -ne 0 ]]; then
  sudo_args=(
    --unit "$UNIT" \
    --run-dir "$RUN_DIR" \
    --source-wing "$SOURCE_WING"
  )
  if [[ "$APPLY_COPIES" -eq 1 ]]; then
    sudo_args+=(--apply-copies)
  fi
  exec sudo env \
    MEMPALACE_ROOT="$ROOT" \
    MEMPALACE_APP="$APP" \
    MEMPALACE_VENV="$VENV" \
    MEMPALACE_ENV_FILE="$ENV_FILE" \
    MEMPALACE_ONTOLOGY_LOCALAI_BASE_URL="$LOCALAI_BASE_URL" \
    MEMPALACE_ONTOLOGY_LOCALAI_TOKEN_FILE="$LOCALAI_TOKEN_FILE" \
    MEMPALACE_ONTOLOGY_LOCALAI_MODEL="$LOCALAI_MODEL" \
    MEMPALACE_ONTOLOGY_MCP_TOKEN_FILE="$MCP_TOKEN_FILE" \
    "$0" "${sudo_args[@]}"
fi

if [[ ! -x "$VENV/bin/mempalace" ]]; then
  echo "missing MemPalace executable: $VENV/bin/mempalace" >&2
  exit 1
fi
if [[ ! -d "$APP" ]]; then
  echo "missing MemPalace app directory: $APP" >&2
  exit 1
fi
if [[ ! -f "$ENV_FILE" ]]; then
  echo "missing MemPalace env file: $ENV_FILE" >&2
  exit 1
fi
if [[ ! -f "$LOCALAI_TOKEN_FILE" ]]; then
  echo "missing LocalAI token file: $LOCALAI_TOKEN_FILE" >&2
  exit 1
fi
if [[ ! -f "$MCP_TOKEN_FILE" ]]; then
  echo "missing MCP token file: $MCP_TOKEN_FILE" >&2
  exit 1
fi
if systemctl is-active --quiet "$UNIT"; then
  echo "ontology runner unit is already active: $UNIT" >&2
  exit 3
fi

# shellcheck disable=SC1090
source "$ENV_FILE"
http_host="${MEMPALACE_HTTP_HOST:-127.0.0.1}"
http_port="${MEMPALACE_HTTP_PORT:-8765}"
MCP_URL="${MEMPALACE_ONTOLOGY_MCP_URL:-http://$http_host:$http_port}"

install -d -o mempalace -g mempalace -m 0750 "$RUN_DIR"

cmd=(
  "$VENV/bin/mempalace"
  ontology chatgpt-signals
  --no-dry-run
  --run
  --run-dir "$RUN_DIR"
  --source-wing "$SOURCE_WING"
)
if [[ "$APPLY_COPIES" -eq 1 ]]; then
  cmd+=(--apply-copies)
fi

systemd-run \
  --unit="$UNIT" \
  --description="MemPalace ChatGPT signal ontology runner" \
  --collect \
  --property=User=mempalace \
  --property=Group=mempalace \
  --property=WorkingDirectory="$APP" \
  --property=EnvironmentFile="$ENV_FILE" \
  --property=MemoryMax=16G \
  --property=CPUQuota=200% \
  --property=Nice=10 \
  --property=IOSchedulingClass=best-effort \
  --property=IOSchedulingPriority=7 \
  --property=NoNewPrivileges=true \
  --property=ProtectSystem=strict \
  --property=ReadWritePaths="$ROOT" \
  --setenv=PYTHONPATH="$APP" \
  --setenv=MEMPALACE_ONTOLOGY_RUN_ROOT="$RUN_DIR" \
  --setenv=MEMPALACE_ONTOLOGY_SOURCE_WING="$SOURCE_WING" \
  --setenv=MEMPALACE_ONTOLOGY_LOCALAI_BASE_URL="$LOCALAI_BASE_URL" \
  --setenv=MEMPALACE_ONTOLOGY_LOCALAI_TOKEN_FILE="$LOCALAI_TOKEN_FILE" \
  --setenv=MEMPALACE_ONTOLOGY_LOCALAI_MODEL="$LOCALAI_MODEL" \
  --setenv=MEMPALACE_ONTOLOGY_MCP_URL="$MCP_URL" \
  --setenv=MEMPALACE_ONTOLOGY_MCP_TOKEN_FILE="$MCP_TOKEN_FILE" \
  "${cmd[@]}"

cat <<EOF
Ontology runner submitted.

Unit:      $UNIT
Run root:  $RUN_DIR
Progress:  $RUN_DIR/<run_id>/progress.json
Journal:   journalctl -fu $UNIT

Apply copies: $APPLY_COPIES
EOF
