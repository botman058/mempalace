#!/usr/bin/env bash
set -euo pipefail

ROOT="${MEMPALACE_ROOT:-/media/u0/OneDrive_Backup/mempalace}"
APP="${MEMPALACE_APP:-$ROOT/app}"
VENV="${MEMPALACE_VENV:-$ROOT/venv}"
STAGE=""

usage() {
  cat <<'USAGE'
Usage: scripts/systemd/promote_snow_white_iii_app_update.sh --stage PATH

Promotes a staged MemPalace app tree into the canonical snow-white-iii app
directory without deleting existing files. This is the update path for installs
where /media/u0/OneDrive_Backup/mempalace/app is a staged copy, not a git
checkout.

Safety:
  - refuses hosts other than snow-white-iii unless explicitly overridden
  - refuses /media/u0/Extreme SSD
  - copies only into the canonical app directory
  - never passes rsync --delete
  - does not touch palace data, sources, cache, logs, secrets, or services
USAGE
}

while (($#)); do
  case "$1" in
    --stage)
      STAGE="${2:?--stage requires a staged app path}"
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

if [[ -z "$STAGE" ]]; then
  echo "--stage is required" >&2
  usage >&2
  exit 2
fi

host_lc="$(hostname | tr '[:upper:]' '[:lower:]')"
if [[ "$host_lc" != "snow-white-iii" && "$host_lc" != "snow-white-iii.local" && "${MEMPALACE_INSTALL_ALLOW_OTHER_HOST:-}" != "1" ]]; then
  echo "refusing promotion on host '$(hostname)'; expected snow-white-iii" >&2
  exit 2
fi

for path in "$ROOT" "$APP" "$VENV" "$STAGE"; do
  case "$path" in
    /media/u0/Extreme\ SSD|/media/u0/Extreme\ SSD/*)
      echo "refusing to use /media/u0/Extreme SSD: $path" >&2
      exit 2
      ;;
  esac
done

if [[ "$EUID" -ne 0 ]]; then
  exec sudo env \
    MEMPALACE_ROOT="$ROOT" \
    MEMPALACE_APP="$APP" \
    MEMPALACE_VENV="$VENV" \
    "$0" --stage "$STAGE"
fi

if ! getent passwd mempalace >/dev/null; then
  echo "missing mempalace service user" >&2
  exit 1
fi
if ! getent group mempalace >/dev/null; then
  echo "missing mempalace service group" >&2
  exit 1
fi
if [[ ! -d "$STAGE" ]]; then
  echo "staged app path does not exist: $STAGE" >&2
  exit 1
fi
if [[ ! -f "$STAGE/pyproject.toml" || ! -f "$STAGE/mempalace/cli.py" ]]; then
  echo "staged app path does not look like a MemPalace repo tree: $STAGE" >&2
  exit 1
fi
if [[ ! -x "$VENV/bin/python" || ! -x "$VENV/bin/mempalace" ]]; then
  echo "missing MemPalace venv executables under $VENV" >&2
  exit 1
fi
if ! command -v rsync >/dev/null 2>&1; then
  echo "rsync is required to promote the staged app" >&2
  exit 1
fi

install -d -o mempalace -g mempalace -m 0750 "$APP"

rsync -a \
  --exclude .git \
  --exclude .venv \
  --exclude .pytest_cache \
  "$STAGE"/ "$APP"/
chown -R mempalace:mempalace "$APP"

runuser -u mempalace -- env PYTHONPATH="$APP" "$VENV/bin/python" -m py_compile \
  "$APP/mempalace/cli.py" \
  "$APP/mempalace/ontology_runner.py" \
  "$APP/mempalace/ontology_run.py"
runuser -u mempalace -- env PYTHONPATH="$APP" "$VENV/bin/mempalace" \
  ontology chatgpt-signals --help >/dev/null

cat <<EOF
MemPalace app promotion complete.

Staged app: $STAGE
Live app:   $APP
Venv:       $VENV

No files were deleted, no services were restarted, and palace data was not
touched.
EOF
