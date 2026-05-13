#!/usr/bin/env bash
set -euo pipefail

CANONICAL_ROOT="/media/u0/OneDrive_Backup/mempalace"
CANONICAL_LOCALAI_BASE_URL="http://snow-white-iii:8080/v1"
CANONICAL_ATLAS_RUN_DIR="$CANONICAL_ROOT/data/chatgpt_archive_atlas/atlas_full2_20260512T0412Z_2fc8ac5"
ROOT="${MEMPALACE_ROOT:-$CANONICAL_ROOT}"
APP="${MEMPALACE_APP:-$ROOT/app}"
VENV="${MEMPALACE_VENV:-$ROOT/venv}"
SCRIPT="${MEMPALACE_CHATGPT_ATLAS_GUIDED_SCRIPT:-$APP/scripts/localai_chatgpt_thread_signals.py}"
SOURCE_DIR="${MEMPALACE_CHATGPT_ATLAS_GUIDED_SOURCE_DIR:-$ROOT/sources/chatgpt}"
ATLAS_RUN_ROOT="${MEMPALACE_CHATGPT_ARCHIVE_ATLAS_RUN_ROOT:-$ROOT/data/chatgpt_archive_atlas}"
ATLAS_RUN_DIR="${MEMPALACE_CHATGPT_ATLAS_GUIDED_ATLAS_RUN_DIR:-$CANONICAL_ATLAS_RUN_DIR}"
RUN_ROOT="${MEMPALACE_CHATGPT_ATLAS_GUIDED_RUN_ROOT:-$ROOT/data/atlas_guided_chatgpt_signals}"
RUN_DIR_ARG="${MEMPALACE_CHATGPT_ATLAS_GUIDED_RUN_DIR:-}"
RUN_ID="${MEMPALACE_CHATGPT_ATLAS_GUIDED_RUN_ID:-}"
LOCALAI_BASE_URL="${MEMPALACE_CHATGPT_ATLAS_GUIDED_LOCALAI_BASE_URL:-$CANONICAL_LOCALAI_BASE_URL}"
LOCALAI_TOKEN_FILE="${MEMPALACE_CHATGPT_ATLAS_GUIDED_LOCALAI_TOKEN_FILE:-$ROOT/secrets/localai_token}"
CANDIDATE_RECORDS="${MEMPALACE_CHATGPT_ATLAS_GUIDED_CANDIDATE_RECORDS:-}"
UNIT_BASE="${MEMPALACE_CHATGPT_ATLAS_GUIDED_UNIT_BASE:-mempalace-chatgpt-atlas-guided}"
UNIT="${MEMPALACE_CHATGPT_ATLAS_GUIDED_UNIT:-}"
LIMIT="${MEMPALACE_CHATGPT_ATLAS_GUIDED_LIMIT:-}"
RETRY_ERRORS="${MEMPALACE_CHATGPT_ATLAS_GUIDED_RETRY_ERRORS:-0}"
PROVIDER_MAX_ATTEMPTS="${MEMPALACE_CHATGPT_ATLAS_GUIDED_PROVIDER_MAX_ATTEMPTS:-2}"
MODEL="${MEMPALACE_CHATGPT_ATLAS_GUIDED_MODEL:-qwen3-vl-8b-instruct}"
SCRIPT_PATH="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/$(basename "${BASH_SOURCE[0]}")"

usage() {
  cat <<'USAGE'
Usage: scripts/systemd/start_chatgpt_atlas_guided_extraction_snow_white_iii.sh [options]

Starts the WP-05 atlas-guided ChatGPT no-publish extraction pass on
snow-white-iii as the mempalace service user in a bounded transient systemd
unit with CPUQuota=200% and MemoryMax=16G.

Options:
  --atlas-run-dir PATH       Atlas run directory (default: canonical full2 run)
  --candidate-records PATH   Optional override for candidate_bridge_records.jsonl
  --run-id ID                Create or resume RUN_ROOT/ID
  --run-dir PATH             Explicit run directory under the canonical guided root
  --limit N                  Process at most N segments
  --retry-errors             Retry checkpointed provider_error rows
  --provider-max-attempts N  LocalAI classify attempts per segment (default: 2)

This wrapper always passes --atlas-guided, never passes --publish, refuses
/media/u0/Extreme SSD, refuses non-local LocalAI URLs, and never restarts
services or deletes data.
USAGE
}

while (($#)); do
  case "$1" in
    --atlas-run-dir)
      ATLAS_RUN_DIR="${2:?--atlas-run-dir requires a path}"
      shift 2
      ;;
    --candidate-records)
      CANDIDATE_RECORDS="${2:?--candidate-records requires a path}"
      shift 2
      ;;
    --run-id)
      RUN_ID="${2:?--run-id requires a value}"
      shift 2
      ;;
    --run-dir)
      RUN_DIR_ARG="${2:?--run-dir requires a path}"
      shift 2
      ;;
    --limit)
      LIMIT="${2:?--limit requires a value}"
      shift 2
      ;;
    --retry-errors)
      RETRY_ERRORS=1
      shift
      ;;
    --provider-max-attempts)
      PROVIDER_MAX_ATTEMPTS="${2:?--provider-max-attempts requires a value}"
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
if [[ "$host_lc" != "snow-white-iii" && "$host_lc" != "snow-white-iii.local" ]]; then
  echo "refusing atlas-guided extraction start on host '$(hostname)'; expected snow-white-iii" >&2
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

require_within() {
  local label="$1"
  local parent="$2"
  local child="$3"
  local parent_resolved child_resolved
  parent_resolved="$(realpath -m "$parent")"
  child_resolved="$(realpath -m "$child")"
  if [[ "$child_resolved" != "$parent_resolved" && "$child_resolved" != "$parent_resolved/"* ]]; then
    echo "$label must stay under $parent_resolved" >&2
    echo "got: $child_resolved" >&2
    exit 2
  fi
}

normalize_localai_base_url() {
  local value="$1"
  local normalized="${value%/}"
  local lowered
  lowered="$(printf '%s' "$normalized" | tr '[:upper:]' '[:lower:]')"
  for blocked in \
    "api.openai.com" \
    "anthropic.com" \
    "openrouter.ai" \
    "together.xyz" \
    "groq.com" \
    "generativelanguage.googleapis.com" \
    "vertexai.googleapis.com"; do
    if [[ "$lowered" == *"$blocked"* ]]; then
      echo "refusing non-local LocalAI provider URL: $blocked" >&2
      exit 2
    fi
  done
  if [[ "$normalized" != "$CANONICAL_LOCALAI_BASE_URL" ]]; then
    echo "refusing LocalAI base URL: expected $CANONICAL_LOCALAI_BASE_URL" >&2
    echo "got: $value" >&2
    exit 2
  fi
  printf '%s\n' "$normalized"
}

ROOT_RESOLVED="$(realpath -m "$ROOT")"
CANONICAL_ROOT_RESOLVED="$(realpath -m "$CANONICAL_ROOT")"
if [[ "$ROOT_RESOLVED" != "$CANONICAL_ROOT_RESOLVED" ]]; then
  echo "refusing non-canonical MemPalace root: $ROOT" >&2
  exit 2
fi

if [[ -n "$RUN_DIR_ARG" && -n "$RUN_ID" ]]; then
  echo "use either --run-id or --run-dir, not both" >&2
  exit 2
fi

if [[ -z "$RUN_ID" && -z "$RUN_DIR_ARG" ]]; then
  RUN_ID="atlas_guided_$(date -u +%Y%m%dT%H%M%SZ)"
fi

if [[ -n "$RUN_ID" ]]; then
  if [[ "$RUN_ID" == "." || "$RUN_ID" == ".." || "$RUN_ID" == *"/"* || "$RUN_ID" == *"\\"* ]]; then
    echo "run id must be a simple slug with no path separators: $RUN_ID" >&2
    exit 2
  fi
  if [[ ! "$RUN_ID" =~ ^[A-Za-z0-9][A-Za-z0-9_.-]{0,79}$ ]]; then
    echo "run id must match ^[A-Za-z0-9][A-Za-z0-9_.-]{0,79}$: $RUN_ID" >&2
    exit 2
  fi
  RUN_DIR="$RUN_ROOT/$RUN_ID"
else
  RUN_DIR="$RUN_DIR_ARG"
fi

if [[ -z "$CANDIDATE_RECORDS" ]]; then
  CANDIDATE_RECORDS="$ATLAS_RUN_DIR/candidate_bridge_records.jsonl"
fi

ATLAS_THREAD_CANDIDATES="$ATLAS_RUN_DIR/atlas_thread_candidates.jsonl"
ATLAS_COVERAGE_REPORT="$ATLAS_RUN_DIR/atlas_candidate_coverage.json"
ATLAS_THREAD_INDEX="$ATLAS_RUN_DIR/thread_index.jsonl"

for path in \
  "$ROOT" \
  "$APP" \
  "$VENV" \
  "$SCRIPT" \
  "$SOURCE_DIR" \
  "$ATLAS_RUN_ROOT" \
  "$ATLAS_RUN_DIR" \
  "$RUN_ROOT" \
  "$RUN_DIR" \
  "$LOCALAI_TOKEN_FILE" \
  "$CANDIDATE_RECORDS" \
  "$ATLAS_THREAD_CANDIDATES" \
  "$ATLAS_COVERAGE_REPORT" \
  "$ATLAS_THREAD_INDEX"; do
  refuse_extreme_ssd "$path"
done

require_within "app directory" "$ROOT" "$APP"
require_within "venv directory" "$ROOT" "$VENV"
require_within "runner script" "$APP" "$SCRIPT"
require_within "source directory" "$ROOT" "$SOURCE_DIR"
require_within "atlas run root" "$ROOT" "$ATLAS_RUN_ROOT"
require_within "atlas run directory" "$ATLAS_RUN_ROOT" "$ATLAS_RUN_DIR"
require_within "guided run root" "$ROOT" "$RUN_ROOT"
require_within "guided run directory" "$RUN_ROOT" "$RUN_DIR"
require_within "candidate records" "$ATLAS_RUN_DIR" "$CANDIDATE_RECORDS"
require_within "atlas thread candidates" "$ATLAS_RUN_DIR" "$ATLAS_THREAD_CANDIDATES"
require_within "atlas candidate coverage" "$ATLAS_RUN_DIR" "$ATLAS_COVERAGE_REPORT"
require_within "atlas thread index" "$ATLAS_RUN_DIR" "$ATLAS_THREAD_INDEX"

LOCALAI_BASE_URL="$(normalize_localai_base_url "$LOCALAI_BASE_URL")"
CANONICAL_LOCALAI_TOKEN_FILE="$(realpath -m "$ROOT/secrets/localai_token")"
LOCALAI_TOKEN_FILE_RESOLVED="$(realpath -m "$LOCALAI_TOKEN_FILE")"
if [[ "$LOCALAI_TOKEN_FILE_RESOLVED" != "$CANONICAL_LOCALAI_TOKEN_FILE" ]]; then
  echo "refusing non-canonical LocalAI token file: $LOCALAI_TOKEN_FILE" >&2
  exit 2
fi

if [[ -n "$LIMIT" ]] && [[ ! "$LIMIT" =~ ^[0-9]+$ ]]; then
  echo "invalid --limit value: $LIMIT" >&2
  exit 2
fi
if [[ ! "$PROVIDER_MAX_ATTEMPTS" =~ ^[0-9]+$ ]] || [[ "$PROVIDER_MAX_ATTEMPTS" -lt 1 ]]; then
  echo "invalid --provider-max-attempts value: $PROVIDER_MAX_ATTEMPTS" >&2
  exit 2
fi

RUN_DIR_RESOLVED="$(realpath -m "$RUN_DIR")"
RUN_DIR_BASENAME="$(basename "$RUN_DIR_RESOLVED")"
UNIT_SLUG="$(printf '%s' "$RUN_DIR_BASENAME" | tr -c 'A-Za-z0-9_.-' '_')"
UNIT_SLUG="${UNIT_SLUG##_}"
UNIT_SLUG="${UNIT_SLUG%%_}"
if [[ -z "$UNIT_SLUG" ]]; then
  UNIT_SLUG="atlas_guided_$(date -u +%Y%m%d%H%M%S)"
fi
if [[ -z "$UNIT" ]]; then
  UNIT="${UNIT_BASE}-${UNIT_SLUG}"
fi

if [[ "$EUID" -ne 0 ]]; then
  sudo_args=(--atlas-run-dir "$ATLAS_RUN_DIR" --provider-max-attempts "$PROVIDER_MAX_ATTEMPTS")
  if [[ -n "$CANDIDATE_RECORDS" ]]; then
    sudo_args+=(--candidate-records "$CANDIDATE_RECORDS")
  fi
  if [[ -n "$RUN_ID" ]]; then
    sudo_args+=(--run-id "$RUN_ID")
  fi
  if [[ -n "$RUN_DIR_ARG" ]]; then
    sudo_args+=(--run-dir "$RUN_DIR_ARG")
  fi
  if [[ -n "$LIMIT" ]]; then
    sudo_args+=(--limit "$LIMIT")
  fi
  if [[ "$RETRY_ERRORS" == "1" ]]; then
    sudo_args+=(--retry-errors)
  fi
  exec sudo env \
    MEMPALACE_ROOT="$ROOT" \
    MEMPALACE_APP="$APP" \
    MEMPALACE_VENV="$VENV" \
    MEMPALACE_CHATGPT_ATLAS_GUIDED_SCRIPT="$SCRIPT" \
    MEMPALACE_CHATGPT_ATLAS_GUIDED_SOURCE_DIR="$SOURCE_DIR" \
    MEMPALACE_CHATGPT_ARCHIVE_ATLAS_RUN_ROOT="$ATLAS_RUN_ROOT" \
    MEMPALACE_CHATGPT_ATLAS_GUIDED_ATLAS_RUN_DIR="$ATLAS_RUN_DIR" \
    MEMPALACE_CHATGPT_ATLAS_GUIDED_RUN_ROOT="$RUN_ROOT" \
    MEMPALACE_CHATGPT_ATLAS_GUIDED_RUN_DIR="$RUN_DIR_ARG" \
    MEMPALACE_CHATGPT_ATLAS_GUIDED_RUN_ID="$RUN_ID" \
    MEMPALACE_CHATGPT_ATLAS_GUIDED_LOCALAI_BASE_URL="$LOCALAI_BASE_URL" \
    MEMPALACE_CHATGPT_ATLAS_GUIDED_LOCALAI_TOKEN_FILE="$LOCALAI_TOKEN_FILE" \
    MEMPALACE_CHATGPT_ATLAS_GUIDED_CANDIDATE_RECORDS="$CANDIDATE_RECORDS" \
    MEMPALACE_CHATGPT_ATLAS_GUIDED_UNIT_BASE="$UNIT_BASE" \
    MEMPALACE_CHATGPT_ATLAS_GUIDED_UNIT="$UNIT" \
    MEMPALACE_CHATGPT_ATLAS_GUIDED_LIMIT="$LIMIT" \
    MEMPALACE_CHATGPT_ATLAS_GUIDED_RETRY_ERRORS="$RETRY_ERRORS" \
    MEMPALACE_CHATGPT_ATLAS_GUIDED_PROVIDER_MAX_ATTEMPTS="$PROVIDER_MAX_ATTEMPTS" \
    MEMPALACE_CHATGPT_ATLAS_GUIDED_MODEL="$MODEL" \
    "$SCRIPT_PATH" "${sudo_args[@]}"
fi

if [[ ! -f "$SCRIPT" ]]; then
  echo "missing atlas-guided extraction script: $SCRIPT" >&2
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
if [[ ! -d "$ATLAS_RUN_DIR" ]]; then
  echo "missing atlas run directory: $ATLAS_RUN_DIR" >&2
  exit 1
fi
if [[ ! -f "$CANDIDATE_RECORDS" ]]; then
  echo "missing candidate bridge records: $CANDIDATE_RECORDS" >&2
  exit 1
fi
if [[ ! -f "$ATLAS_THREAD_CANDIDATES" ]]; then
  echo "missing atlas thread candidates: $ATLAS_THREAD_CANDIDATES" >&2
  exit 1
fi
if [[ ! -f "$ATLAS_COVERAGE_REPORT" ]]; then
  echo "missing atlas candidate coverage report: $ATLAS_COVERAGE_REPORT" >&2
  exit 1
fi
if [[ ! -f "$ATLAS_THREAD_INDEX" ]]; then
  echo "missing atlas thread index: $ATLAS_THREAD_INDEX" >&2
  exit 1
fi
if [[ ! -f "$LOCALAI_TOKEN_FILE" ]]; then
  echo "missing LocalAI token file: $LOCALAI_TOKEN_FILE" >&2
  exit 1
fi
if systemctl is-active --quiet "$UNIT"; then
  echo "atlas-guided extraction unit is already active: $UNIT" >&2
  exit 3
fi

install -d -o mempalace -g mempalace -m 0750 "$RUN_ROOT"
install -d -o mempalace -g mempalace -m 0750 "$RUN_DIR"

cmd=(
  "$VENV/bin/python"
  "$SCRIPT"
  --source-dir "$SOURCE_DIR"
  --run-dir "$RUN_DIR"
  --atlas-guided
  --atlas-run-dir "$ATLAS_RUN_DIR"
  --candidate-records "$CANDIDATE_RECORDS"
  --localai-base-url "$LOCALAI_BASE_URL"
  --localai-token-file "$LOCALAI_TOKEN_FILE"
  --provider-max-attempts "$PROVIDER_MAX_ATTEMPTS"
)
if [[ "$RETRY_ERRORS" == "1" ]]; then
  cmd+=(--retry-errors)
fi
if [[ -n "$LIMIT" ]]; then
  cmd+=(--limit "$LIMIT")
fi

systemd-run \
  --unit="$UNIT" \
  --description="MemPalace atlas-guided ChatGPT no-publish extraction" \
  --collect \
  --property=User=mempalace \
  --property=Group=mempalace \
  --property=WorkingDirectory="$APP" \
  --property=NoNewPrivileges=true \
  --property=ProtectSystem=strict \
  --property=ReadWritePaths="$RUN_DIR" \
  --property=MemoryMax=16G \
  --property=CPUQuota=200% \
  --property=Nice=10 \
  --property=IOSchedulingClass=best-effort \
  --property=IOSchedulingPriority=7 \
  --setenv=PYTHONPATH="$APP" \
  --setenv=MEMPALACE_ROOT="$ROOT" \
  --setenv=MEMPALACE_APP="$APP" \
  --setenv=MEMPALACE_VENV="$VENV" \
  --setenv=CHATGPT_SOURCE_DIR="$SOURCE_DIR" \
  --setenv=CHATGPT_ATLAS_RUN_DIR="$ATLAS_RUN_DIR" \
  --setenv=CHATGPT_ATLAS_CANDIDATE_RECORDS="$CANDIDATE_RECORDS" \
  --setenv=LOCALAI_BASE_URL="$LOCALAI_BASE_URL" \
  --setenv=LOCALAI_TOKEN_FILE="$LOCALAI_TOKEN_FILE" \
  --setenv=LOCALAI_MODEL="$MODEL" \
  --setenv=LOCALAI_THREAD_SIGNAL_ATLAS_GUIDED=1 \
  --setenv=LOCALAI_THREAD_SIGNAL_RUN_DIR="$RUN_DIR" \
  --setenv=LOCALAI_THREAD_SIGNAL_RETRY_ERRORS="$RETRY_ERRORS" \
  --setenv=LOCALAI_THREAD_SIGNAL_PROVIDER_MAX_ATTEMPTS="$PROVIDER_MAX_ATTEMPTS" \
  "${cmd[@]}"

cat <<EOF
Atlas-guided ChatGPT extraction submitted.

Unit:      $UNIT
Run dir:   $RUN_DIR
Atlas run: $ATLAS_RUN_DIR
Progress:  $RUN_DIR/progress.json
Artifacts: $RUN_DIR/extraction_records.jsonl
           $RUN_DIR/invalid_outputs.jsonl
           $RUN_DIR/reconciled_signals.jsonl
           $RUN_DIR/publish_checkpoint.jsonl
Retry errors: $RETRY_ERRORS
Provider max attempts: $PROVIDER_MAX_ATTEMPTS
Journal:   journalctl -fu $UNIT
EOF
