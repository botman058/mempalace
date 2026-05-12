#!/usr/bin/env bash
set -euo pipefail

ROOT="${MEMPALACE_ROOT:-/media/u0/OneDrive_Backup/mempalace}"
APP="${MEMPALACE_APP:-$ROOT/app}"
VENV="${MEMPALACE_VENV:-$ROOT/venv}"
SCRIPT="${MEMPALACE_CHATGPT_ARCHIVE_ATLAS_SCRIPT:-$APP/mempalace/chatgpt_archive_atlas_runner.py}"
SOURCE_DIR="${MEMPALACE_CHATGPT_ARCHIVE_ATLAS_SOURCE_DIR:-$ROOT/sources/chatgpt}"
RUN_ROOT="${MEMPALACE_CHATGPT_ARCHIVE_ATLAS_RUN_ROOT:-$ROOT/data/chatgpt_archive_atlas}"
RUN_ID="${MEMPALACE_CHATGPT_ARCHIVE_ATLAS_RUN_ID:-atlas_$(date -u +%Y%m%d%H%M%S)}"
UNIT_BASE="${MEMPALACE_CHATGPT_ARCHIVE_ATLAS_UNIT_BASE:-mempalace-chatgpt-archive-atlas}"
UNIT="${MEMPALACE_CHATGPT_ARCHIVE_ATLAS_UNIT:-}"
LIMIT="${MEMPALACE_CHATGPT_ARCHIVE_ATLAS_LIMIT:-}"
ATLAS_LD_LIBRARY_PATH="${MEMPALACE_CHATGPT_ARCHIVE_ATLAS_LD_LIBRARY_PATH:-}"
SCRIPT_PATH="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/$(basename "${BASH_SOURCE[0]}")"

usage() {
  cat <<'USAGE'
Usage: scripts/systemd/start_chatgpt_archive_atlas_snow_white_iii.sh [options]

Starts a pre-LLM ChatGPT archive atlas run on snow-white-iii as the mempalace
service user in a bounded transient systemd unit.

Options:
  --source-dir PATH  ChatGPT export root (default: canonical sources/chatgpt)
  --run-root PATH    Atlas run root (default: canonical data/chatgpt_archive_atlas)
  --run-id ID        Explicit run id (default: atlas_<utc timestamp>)
  --limit N          Bounded smoke run size for the atlas runner

This wrapper is artifact-only: no LocalAI, no cloud calls, no MCP publish args.
It refuses /media/u0/Extreme SSD paths and never deletes data or restarts services.
USAGE
}

while (($#)); do
  case "$1" in
    --source-dir)
      SOURCE_DIR="${2:?--source-dir requires a path}"
      shift 2
      ;;
    --run-root)
      RUN_ROOT="${2:?--run-root requires a path}"
      shift 2
      ;;
    --run-id)
      RUN_ID="${2:?--run-id requires a value}"
      shift 2
      ;;
    --limit)
      LIMIT="${2:?--limit requires a value}"
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
  echo "refusing atlas runner start on host '$(hostname)'; expected snow-white-iii" >&2
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

if [[ -z "$RUN_ID" ]]; then
  echo "run id must not be empty" >&2
  exit 2
fi
if [[ "$RUN_ID" == "." || "$RUN_ID" == ".." || "$RUN_ID" == *"/"* || "$RUN_ID" == *"\\"* ]]; then
  echo "run id must be a simple slug with no path separators: $RUN_ID" >&2
  exit 2
fi
if [[ ! "$RUN_ID" =~ ^[A-Za-z0-9][A-Za-z0-9_.-]{0,79}$ ]]; then
  echo "run id must match ^[A-Za-z0-9][A-Za-z0-9_.-]{0,79}$: $RUN_ID" >&2
  exit 2
fi

RUN_DIR="$RUN_ROOT/$RUN_ID"

for path in "$ROOT" "$APP" "$VENV" "$SCRIPT" "$SOURCE_DIR" "$RUN_ROOT" "$RUN_DIR"; do
  refuse_extreme_ssd "$path"
done

RUN_ROOT_RESOLVED="$(realpath -m "$RUN_ROOT")"
RUN_DIR_RESOLVED="$(realpath -m "$RUN_DIR")"
refuse_extreme_ssd "$RUN_ROOT_RESOLVED"
refuse_extreme_ssd "$RUN_DIR_RESOLVED"
if [[ "$RUN_DIR_RESOLVED" != "$RUN_ROOT_RESOLVED" && "$RUN_DIR_RESOLVED" != "$RUN_ROOT_RESOLVED/"* ]]; then
  echo "run directory must be contained under run root" >&2
  echo "run_root=$RUN_ROOT_RESOLVED" >&2
  echo "run_dir=$RUN_DIR_RESOLVED" >&2
  exit 2
fi

RUN_ROOT="$RUN_ROOT_RESOLVED"
RUN_DIR="$RUN_DIR_RESOLVED"

if [[ -n "$LIMIT" ]] && [[ ! "$LIMIT" =~ ^[0-9]+$ ]]; then
  echo "invalid --limit value: $LIMIT" >&2
  exit 2
fi

if [[ -z "$UNIT" ]]; then
  UNIT="${UNIT_BASE}-${RUN_ID}"
fi

if [[ "$EUID" -ne 0 ]]; then
  exec sudo env \
    MEMPALACE_ROOT="$ROOT" \
    MEMPALACE_APP="$APP" \
    MEMPALACE_VENV="$VENV" \
    MEMPALACE_CHATGPT_ARCHIVE_ATLAS_SCRIPT="$SCRIPT" \
    MEMPALACE_CHATGPT_ARCHIVE_ATLAS_SOURCE_DIR="$SOURCE_DIR" \
    MEMPALACE_CHATGPT_ARCHIVE_ATLAS_RUN_ROOT="$RUN_ROOT" \
    MEMPALACE_CHATGPT_ARCHIVE_ATLAS_RUN_ID="$RUN_ID" \
    MEMPALACE_CHATGPT_ARCHIVE_ATLAS_UNIT_BASE="$UNIT_BASE" \
    MEMPALACE_CHATGPT_ARCHIVE_ATLAS_UNIT="$UNIT" \
    MEMPALACE_CHATGPT_ARCHIVE_ATLAS_LIMIT="$LIMIT" \
    MEMPALACE_CHATGPT_ARCHIVE_ATLAS_LD_LIBRARY_PATH="$ATLAS_LD_LIBRARY_PATH" \
    "$SCRIPT_PATH"
fi

if [[ ! -f "$SCRIPT" ]]; then
  echo "missing atlas runner script: $SCRIPT" >&2
  echo "expected future path under staged app; deploy runner module before launch" >&2
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

if [[ -z "$ATLAS_LD_LIBRARY_PATH" ]]; then
  site_lib="$("$VENV/bin/python" - <<'PY'
import site
paths = site.getsitepackages()
print(paths[0] if paths else "")
PY
)"

  cuda_dirs=()
  if [[ -n "$site_lib" ]]; then
    for dir in \
      "$site_lib"/nvidia/cublas/lib \
      "$site_lib"/nvidia/cuda_cupti/lib \
      "$site_lib"/nvidia/cuda_nvrtc/lib \
      "$site_lib"/nvidia/cuda_runtime/lib \
      "$site_lib"/nvidia/cudnn/lib \
      "$site_lib"/nvidia/cufft/lib \
      "$site_lib"/nvidia/curand/lib \
      "$site_lib"/nvidia/cusolver/lib \
      "$site_lib"/nvidia/cusparse/lib \
      "$site_lib"/nvidia/nccl/lib \
      "$site_lib"/nvidia/nvjitlink/lib \
      "$site_lib"/nvidia/nvtx/lib; do
      [[ -d "$dir" ]] && cuda_dirs+=("$dir")
    done
  fi

  if ((${#cuda_dirs[@]})); then
    IFS=:
    ATLAS_LD_LIBRARY_PATH="${cuda_dirs[*]}"
    unset IFS
  else
    echo "missing CUDA/cuDNN runtime libraries under venv site-packages nvidia/*/lib" >&2
    echo "refusing atlas smoke start without LD_LIBRARY_PATH (WP-13 requires CUDA embedding proof)" >&2
    exit 1
  fi
fi

if [[ -z "$ATLAS_LD_LIBRARY_PATH" ]]; then
  echo "computed empty LD_LIBRARY_PATH for atlas runner; refusing to start" >&2
  exit 1
fi

install -d -o mempalace -g mempalace -m 0750 "$RUN_ROOT"
install -d -o mempalace -g mempalace -m 0750 "$RUN_DIR"

cmd=(
  "$VENV/bin/python"
  -m
  mempalace.chatgpt_archive_atlas_runner
  --source-dir "$SOURCE_DIR"
  --run-root "$RUN_ROOT"
  --run-id "$RUN_ID"
)
if [[ -n "$LIMIT" ]]; then
  cmd+=(--limit "$LIMIT")
fi

systemd-run \
  --unit="$UNIT" \
  --description="MemPalace pre-LLM ChatGPT archive atlas run" \
  --collect \
  --property=User=mempalace \
  --property=Group=mempalace \
  --property=WorkingDirectory="$APP" \
  --property=NoNewPrivileges=true \
  --property=ProtectSystem=strict \
  --property=ReadWritePaths="$RUN_ROOT" \
  --property=MemoryMax=16G \
  --property=CPUQuota=200% \
  --property=Nice=10 \
  --property=IOSchedulingClass=best-effort \
  --property=IOSchedulingPriority=7 \
  --setenv=PYTHONPATH="$APP" \
  --setenv=MEMPALACE_ROOT="$ROOT" \
  --setenv=MEMPALACE_APP="$APP" \
  --setenv=MEMPALACE_VENV="$VENV" \
  --setenv=LD_LIBRARY_PATH="$ATLAS_LD_LIBRARY_PATH" \
  --setenv=MEMPALACE_EMBEDDING_DEVICE=cuda \
  --setenv=MEMPALACE_CHATGPT_ARCHIVE_ATLAS_RUN_ROOT="$RUN_ROOT" \
  --setenv=MEMPALACE_CHATGPT_ARCHIVE_ATLAS_RUN_ID="$RUN_ID" \
  "${cmd[@]}"

cat <<EOF
ChatGPT archive atlas runner submitted.

Unit:      $UNIT
Run root:  $RUN_ROOT
Run id:    $RUN_ID
Run dir:   $RUN_DIR
Progress:  $RUN_DIR/progress.json
Journal:   journalctl -fu $UNIT
EOF
