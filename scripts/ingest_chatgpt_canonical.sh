#!/usr/bin/env bash
set -euo pipefail

ROOT="${MEMPALACE_ROOT:-/media/u0/OneDrive_Backup/mempalace}"
VENV="${MEMPALACE_VENV:-$ROOT/venv}"
PALACE="${MEMPALACE_PALACE_PATH:-$ROOT/data/palace}"
SOURCE_IN="${MEMPALACE_SOURCE_ROOT:-$ROOT/sources}/chatgpt"
STAGED="$ROOT/sources/chatgpt"
APPLY=0
ALLOW_EXISTING=0
ALLOW_LEGACY_SIGNALS=0

usage() {
  cat <<'USAGE'
Usage: scripts/ingest_chatgpt_canonical.sh <source-dir> [--apply] [--allow-existing-palace] [--allow-legacy-signals]

Stages ChatGPT exports under the canonical MemPalace source root and mines the
raw chatgpt wing with --extract exchange. The legacy chatgpt_signals pass is
heuristic-only and is disabled unless --allow-legacy-signals is supplied.

Default is a dry run. Use --apply to mine for real. If the canonical palace
already exists, --apply also requires --allow-existing-palace.

For LLM-derived classification, run scripts/localai_chatgpt_signals.py after the
raw exchange mine. Do not use this helper as the semantic classification pass
for a full ChatGPT privacy export.
USAGE
}

args=()
while (($#)); do
  case "$1" in
    --apply)
      APPLY=1
      shift
      ;;
    --allow-existing-palace)
      ALLOW_EXISTING=1
      shift
      ;;
    --allow-legacy-signals)
      ALLOW_LEGACY_SIGNALS=1
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      args+=("$1")
      shift
      ;;
  esac
done

if ((${#args[@]})); then
  SOURCE_IN="${args[0]}"
elif [[ ! -d "$SOURCE_IN" ]]; then
  echo "source-dir is required unless $SOURCE_IN already exists" >&2
  usage >&2
  exit 2
fi

if [[ ! -d "$SOURCE_IN" ]]; then
  echo "source directory does not exist: $SOURCE_IN" >&2
  exit 1
fi
if [[ ! -x "$VENV/bin/mempalace" ]]; then
  echo "mempalace executable not found: $VENV/bin/mempalace" >&2
  exit 1
fi
if ! command -v rsync >/dev/null 2>&1; then
  echo "rsync is required to stage sources" >&2
  exit 1
fi
if [[ "$APPLY" -eq 1 && -e "$PALACE" && "$ALLOW_EXISTING" -ne 1 ]]; then
  echo "canonical palace already exists: $PALACE" >&2
  echo "rerun with --allow-existing-palace after confirming this is intentional" >&2
  exit 3
fi

mkdir -p "$STAGED"
rsync -a "$SOURCE_IN"/ "$STAGED"/

common=("$VENV/bin/mempalace" --palace "$PALACE" mine "$STAGED" --mode convos)
if [[ "$APPLY" -eq 0 ]]; then
  common+=(--dry-run)
fi

"${common[@]}" --wing chatgpt --extract exchange
if [[ "$ALLOW_LEGACY_SIGNALS" -eq 1 ]]; then
  "${common[@]}" --wing chatgpt_signals --extract general
else
  echo
  echo "Skipped chatgpt_signals: legacy --extract general is heuristic-only."
  echo "Use scripts/localai_chatgpt_signals.py for LLM-derived classification."
fi

if [[ "$APPLY" -eq 0 ]]; then
  echo
  echo "Dry run complete. Re-run with --apply to mine into $PALACE."
fi
