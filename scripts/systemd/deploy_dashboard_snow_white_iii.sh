#!/usr/bin/env bash
set -euo pipefail

ROOT="${MEMPALACE_ROOT:-/media/u0/OneDrive_Backup/mempalace}"
APP="$ROOT/app"
VENV="${MEMPALACE_VENV:-$ROOT/venv}"
ENV_FILE="${MEMPALACE_DASHBOARD_ENV_FILE:-$ROOT/mempalace-dashboard.env}"
DASHBOARD_TOKEN_FILE="${MEMPALACE_DASHBOARD_TOKEN_FILE:-$ROOT/secrets/dashboard_token}"
UPSTREAM_TOKEN_FILE="${MEMPALACE_DASHBOARD_MCP_TOKEN_FILE:-${MEMPALACE_HTTP_TOKEN_FILE:-$ROOT/secrets/http_token}}"
UNIT_PATH="/etc/systemd/system/mempalace-dashboard.service"
RUN_PATH="/usr/local/bin/mempalace-dashboard-run"
REMOTE="${MEMPALACE_DASHBOARD_DEPLOY_REMOTE:-root@snow-white-iii}"
START_SERVICE=1
LOCAL_INSTALL=0

usage() {
  cat <<'USAGE'
Usage: scripts/systemd/deploy_dashboard_snow_white_iii.sh [--no-start] [--remote USER@HOST]

Deploys the read-only MemPalace dashboard to snow-white-iii without touching the
running MemPalace HTTP MCP service, mining services, LocalAI, palace data, or
checkpoint files.

When run from another machine, the script copies only dashboard runtime files to
the canonical app directory, then runs its local install step over SSH.

Safety:
  - refuses /media/u0/Extreme SSD
  - stages only dashboard files, not the whole repo
  - creates dashboard_token only if it does not already exist
  - uses existing http_token as the upstream MCP token
  - installs/starts only mempalace-dashboard.service
USAGE
}

while (($#)); do
  case "$1" in
    --no-start)
      START_SERVICE=0
      shift
      ;;
    --remote)
      REMOTE="${2:?--remote requires USER@HOST}"
      shift 2
      ;;
    --local-install)
      LOCAL_INSTALL=1
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

case "$ROOT" in
  /media/u0/Extreme\ SSD|/media/u0/Extreme\ SSD/*)
    echo "refusing to use /media/u0/Extreme SSD" >&2
    exit 2
    ;;
esac

run_root() {
  if [[ "$EUID" -eq 0 ]]; then
    "$@"
  else
    sudo "$@"
  fi
}

run_remote() {
  ssh -o BatchMode=yes "$REMOTE" "$@"
}

ensure_mempalace_account_and_dirs() {
  if ! getent group mempalace >/dev/null; then
    groupadd --system mempalace
  fi
  if ! id -u mempalace >/dev/null 2>&1; then
    useradd --system --gid mempalace --home-dir "$ROOT" --shell /usr/sbin/nologin mempalace
  fi
  if command -v setfacl >/dev/null 2>&1; then
    setfacl -m u:mempalace:rx /media/u0
  else
    echo "setfacl is required so mempalace can traverse /media/u0 without broadening access" >&2
    exit 1
  fi
  install -d -o mempalace -g mempalace -m 0750 "$ROOT" "$APP" "$ROOT/cache" "$ROOT/logs" "$ROOT/tmp"
  install -d -o root -g mempalace -m 0750 "$ROOT/secrets"
}

stage_dashboard_files_remote() {
  if ! command -v rsync >/dev/null 2>&1; then
    echo "rsync is required for remote deployment" >&2
    exit 1
  fi

  run_remote "$(printf '%q ' bash -lc "set -euo pipefail
ROOT='$ROOT'
case \"\$ROOT\" in
  /media/u0/Extreme\\ SSD|/media/u0/Extreme\\ SSD/*) echo 'refusing to use /media/u0/Extreme SSD' >&2; exit 2 ;;
esac
if ! getent group mempalace >/dev/null; then groupadd --system mempalace; fi
if ! id -u mempalace >/dev/null 2>&1; then useradd --system --gid mempalace --home-dir \"\$ROOT\" --shell /usr/sbin/nologin mempalace; fi
if command -v setfacl >/dev/null 2>&1; then setfacl -m u:mempalace:rx /media/u0; else echo 'setfacl is required' >&2; exit 1; fi
install -d -o mempalace -g mempalace -m 0750 \"\$ROOT\" \"\$ROOT/app\" \"\$ROOT/cache\" \"\$ROOT/logs\" \"\$ROOT/tmp\"
install -d -o root -g mempalace -m 0750 \"\$ROOT/secrets\"
")"

  (
    cd "$repo_root"
    rsync -aR --chown=mempalace:mempalace \
      pyproject.toml \
      mempalace/dashboard_server.py \
      mempalace/dashboard_static/ \
      scripts/systemd/mempalace-dashboard-run \
      scripts/systemd/mempalace-dashboard.service \
      scripts/systemd/deploy_dashboard_snow_white_iii.sh \
      "$REMOTE:$APP/"
  )
}

create_dashboard_token_if_missing() {
  if [[ -f "$DASHBOARD_TOKEN_FILE" ]]; then
    return
  fi
  tmp_token="$(mktemp)"
  python3 - <<'PY' >"$tmp_token"
import secrets
print(secrets.token_urlsafe(48))
PY
  run_root install -o root -g mempalace -m 0640 "$tmp_token" "$DASHBOARD_TOKEN_FILE"
  rm -f "$tmp_token"
}

write_env_if_missing() {
  if [[ -f "$ENV_FILE" ]]; then
    return
  fi

  tailnet_ip="${MEMPALACE_DASHBOARD_HOST:-}"
  if [[ -z "$tailnet_ip" ]] && command -v tailscale >/dev/null 2>&1; then
    tailnet_ip="$(tailscale ip -4 2>/dev/null | head -n 1 || true)"
  fi
  if [[ -z "$tailnet_ip" ]]; then
    echo "could not discover Tailscale IPv4 address; set MEMPALACE_DASHBOARD_HOST" >&2
    exit 1
  fi

  tmp_env="$(mktemp)"
  cat >"$tmp_env" <<EOF
MEMPALACE_DASHBOARD_HOST=$tailnet_ip
MEMPALACE_DASHBOARD_PORT=8766
MEMPALACE_DASHBOARD_APP=mempalace.dashboard_server:app
MEMPALACE_DASHBOARD_TOKEN_FILE=$DASHBOARD_TOKEN_FILE
MEMPALACE_DASHBOARD_MCP_URL=http://$tailnet_ip:8765
MEMPALACE_DASHBOARD_MCP_TOKEN_FILE=$UPSTREAM_TOKEN_FILE
LOCALAI_BASE_URL=http://snow-white-iii:8080/v1
LOCALAI_TOKEN_FILE=$ROOT/secrets/localai_token
LOCALAI_SIGNAL_CHECKPOINT=$ROOT/data/localai_chatgpt_signals.checkpoint.jsonl
EOF
  run_root install -o root -g mempalace -m 0640 "$tmp_env" "$ENV_FILE"
  rm -f "$tmp_env"
}

local_install() {
  host_lc="$(hostname | tr '[:upper:]' '[:lower:]')"
  if [[ "$host_lc" != "snow-white-iii" && "$host_lc" != "snow-white-iii.local" && "${MEMPALACE_INSTALL_ALLOW_OTHER_HOST:-}" != "1" ]]; then
    echo "refusing install on host '$(hostname)'; expected snow-white-iii" >&2
    exit 2
  fi

  ensure_mempalace_account_and_dirs

  if [[ ! -x "$VENV/bin/python" ]]; then
    echo "missing MemPalace venv python: $VENV/bin/python" >&2
    exit 1
  fi
  if [[ ! -f "$UPSTREAM_TOKEN_FILE" ]]; then
    echo "missing upstream HTTP MCP token file: $UPSTREAM_TOKEN_FILE" >&2
    exit 1
  fi
  if ! PYTHONPATH="$APP" "$VENV/bin/python" - <<'PY'
import fastapi
import uvicorn
import mempalace.dashboard_server
print("dashboard_import_ok")
PY
  then
    echo "dashboard dependencies are missing from $VENV; install mempalace[server] first" >&2
    exit 1
  fi

  create_dashboard_token_if_missing
  write_env_if_missing

  dashboard_token="$(<"$DASHBOARD_TOKEN_FILE")"
  upstream_token="$(<"$UPSTREAM_TOKEN_FILE")"
  if [[ -z "$dashboard_token" || -z "$upstream_token" ]]; then
    echo "dashboard and upstream tokens must be non-empty" >&2
    exit 1
  fi
  if [[ "$dashboard_token" == "$upstream_token" ]]; then
    echo "dashboard bearer token and upstream MCP bearer token must be distinct" >&2
    exit 1
  fi

  run_root install -o root -g root -m 0755 "$repo_root/scripts/systemd/mempalace-dashboard-run" "$RUN_PATH"
  run_root install -o root -g root -m 0644 "$repo_root/scripts/systemd/mempalace-dashboard.service" "$UNIT_PATH"
  run_root systemd-analyze verify "$UNIT_PATH"
  run_root systemctl daemon-reload

  if [[ "$START_SERVICE" -eq 1 ]]; then
    run_root systemctl enable --now mempalace-dashboard.service
  else
    run_root systemctl enable mempalace-dashboard.service
  fi

  host="$(grep -E '^MEMPALACE_DASHBOARD_HOST=' "$ENV_FILE" | tail -n 1 | cut -d= -f2-)"
  port="$(grep -E '^MEMPALACE_DASHBOARD_PORT=' "$ENV_FILE" | tail -n 1 | cut -d= -f2-)"
  port="${port:-8766}"

  cat <<EOF
MemPalace dashboard deploy complete.

URL:             http://$host:$port/
Unit:            $UNIT_PATH
Run wrapper:     $RUN_PATH
Env:             $ENV_FILE
Dashboard token: $DASHBOARD_TOKEN_FILE
Upstream token:  $UPSTREAM_TOKEN_FILE

The deploy installed/started only mempalace-dashboard.service.
EOF
}

if [[ "$LOCAL_INSTALL" -eq 1 ]]; then
  local_install
  exit 0
fi

stage_dashboard_files_remote
remote_args=(--local-install)
if [[ "$START_SERVICE" -eq 0 ]]; then
  remote_args+=(--no-start)
fi
run_remote "$(printf '%q ' env "MEMPALACE_ROOT=$ROOT" "$APP/scripts/systemd/deploy_dashboard_snow_white_iii.sh" "${remote_args[@]}")"
