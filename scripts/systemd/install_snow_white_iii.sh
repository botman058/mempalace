#!/usr/bin/env bash
set -euo pipefail

ROOT="${MEMPALACE_ROOT:-/media/u0/OneDrive_Backup/mempalace}"
APP="$ROOT/app"
VENV="$ROOT/venv"
PALACE="$ROOT/data/palace"
ENV_FILE="$ROOT/mempalace.env"
TOKEN_FILE="$ROOT/secrets/http_token"
UNIT_PATH="/etc/systemd/system/mempalace-http.service"
RUN_PATH="/usr/local/bin/mempalace-http-run"
START_SERVICE=1

usage() {
  cat <<'USAGE'
Usage: scripts/systemd/install_snow_white_iii.sh [--no-start]

Installs MemPalace as a token-protected HTTP MCP service on snow-white-iii.
The canonical palace path is /media/u0/OneDrive_Backup/mempalace/data/palace.

Safety:
  - aborts unless hostname is snow-white-iii
  - aborts if the canonical palace path already exists
  - stages app files without deleting existing remote files
  - never reads or writes /media/u0/Extreme SSD
USAGE
}

while (($#)); do
  case "$1" in
    --no-start)
      START_SERVICE=0
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

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

run_root() {
  if [[ "$EUID" -eq 0 ]]; then
    "$@"
  else
    sudo "$@"
  fi
}

run_mempalace() {
  if [[ "$EUID" -eq 0 ]]; then
    runuser -u mempalace -- "$@"
  else
    sudo -u mempalace "$@"
  fi
}

host="$(hostname)"
host_lc="${host,,}"
if [[ "$host_lc" != "snow-white-iii" && "${MEMPALACE_INSTALL_ALLOW_OTHER_HOST:-}" != "1" ]]; then
  echo "refusing install on host '$host'; expected snow-white-iii" >&2
  exit 2
fi

case "$ROOT" in
  /media/u0/Extreme\ SSD|/media/u0/Extreme\ SSD/*)
    echo "refusing to use /media/u0/Extreme SSD" >&2
    exit 2
    ;;
esac

if [[ -e "$PALACE" ]]; then
  echo "canonical palace already exists: $PALACE" >&2
  echo "aborting without overwriting it; inspect and confirm a separate plan first" >&2
  exit 3
fi

if ! command -v rsync >/dev/null 2>&1; then
  echo "rsync is required to stage the app directory" >&2
  exit 1
fi

if ! getent group mempalace >/dev/null; then
  run_root groupadd --system mempalace
fi
if ! id -u mempalace >/dev/null 2>&1; then
  run_root useradd --system --gid mempalace --home-dir "$ROOT" --shell /usr/sbin/nologin mempalace
fi

if command -v setfacl >/dev/null 2>&1; then
  run_root setfacl -m u:mempalace:rx /media/u0
else
  echo "setfacl is required so mempalace can traverse /media/u0 without broadening access" >&2
  exit 1
fi

run_root install -d -o mempalace -g mempalace -m 0750 "$ROOT"
run_root install -d -o mempalace -g mempalace -m 0750 "$APP"
run_root install -d -o mempalace -g mempalace -m 0750 "$ROOT/data"
run_root install -d -o mempalace -g mempalace -m 0750 "$ROOT/sources"
run_root install -d -o mempalace -g mempalace -m 0750 "$ROOT/cache"
run_root install -d -o mempalace -g mempalace -m 0750 "$ROOT/tmp"
run_root install -d -o mempalace -g mempalace -m 0750 "$ROOT/logs"
run_root install -d -o root -g mempalace -m 0750 "$ROOT/secrets"

run_root rsync -a \
  --exclude .git \
  --exclude .venv \
  --exclude .pytest_cache \
  "$repo_root"/ "$APP"/
run_root chown -R mempalace:mempalace "$APP"

if [[ ! -x "$VENV/bin/python" ]]; then
  run_mempalace python3 -m venv "$VENV"
fi
run_mempalace "$VENV/bin/python" -m pip install --upgrade pip
run_mempalace "$VENV/bin/python" -m pip install -e "$APP[server,gpu]"
run_mempalace "$VENV/bin/python" -m pip install --force-reinstall "onnxruntime-gpu>=1.16"
run_mempalace "$VENV/bin/python" -m pip install "protobuf<7,>=5"

if [[ ! -f "$ENV_FILE" ]]; then
  run_root install -o root -g mempalace -m 0640 \
    "$repo_root/scripts/systemd/mempalace.env.template" "$ENV_FILE"
  if command -v tailscale >/dev/null 2>&1; then
    tailnet_ip="$(tailscale ip -4 2>/dev/null | head -n 1 || true)"
    if [[ -n "$tailnet_ip" ]]; then
      run_root sed -i "s/^MEMPALACE_HTTP_HOST=.*/MEMPALACE_HTTP_HOST=$tailnet_ip/" "$ENV_FILE"
    fi
  fi
fi

if [[ ! -f "$TOKEN_FILE" ]]; then
  tmp_token="$(mktemp)"
  python3 - <<'PY' >"$tmp_token"
import secrets
print(secrets.token_urlsafe(48))
PY
  run_root install -o root -g mempalace -m 0640 "$tmp_token" "$TOKEN_FILE"
  rm -f "$tmp_token"
fi

run_root install -o root -g root -m 0755 "$repo_root/scripts/systemd/mempalace-http-run" "$RUN_PATH"
run_root install -o root -g root -m 0644 "$repo_root/scripts/systemd/mempalace-http.service" "$UNIT_PATH"
run_root systemctl daemon-reload

if [[ "$START_SERVICE" -eq 1 ]]; then
  run_root systemctl enable --now mempalace-http.service
else
  run_root systemctl enable mempalace-http.service
fi

cat <<EOF
MemPalace HTTP MCP install complete.

Root:      $ROOT
App:       $APP
Venv:      $VENV
Palace:    $PALACE
Token:     $TOKEN_FILE
Unit:      $UNIT_PATH

The palace directory was not created by this installer. Re-mine approved
sources into $PALACE when ready.
EOF
