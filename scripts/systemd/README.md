# MemPalace HTTP MCP systemd deployment

These files support a hosted MemPalace HTTP MCP service for a canonical palace
root on `snow-white-iii`.

Default layout:

```text
/media/u0/OneDrive_Backup/mempalace/
  app/
  venv/
  data/palace/
  sources/
  cache/
  tmp/
  logs/
  secrets/http_token
  secrets/localai_token
```

Install:

```bash
scripts/systemd/install_snow_white_iii.sh --no-start
systemctl start mempalace-http.service
```

The installer:

- creates the `mempalace:mempalace` service account
- stages the app and venv under the canonical root
- stages app files without deleting existing remote files
- installs `mempalace-http.service` and `/usr/local/bin/mempalace-http-run`
- binds to the Tailscale IPv4 address in `mempalace.env`
- refuses `/media/u0/Extreme SSD`
- aborts if `data/palace` already exists
- keeps CUDA/cuDNN library lookup inside the service venv

Service resource controls:

```text
MemoryMax=16G
CPUQuota=200%
Nice=10
IOSchedulingClass=best-effort
IOSchedulingPriority=7
```

Health check:

```bash
TOKEN="$(cat /media/u0/OneDrive_Backup/mempalace/secrets/http_token)"
curl -H "Authorization: Bearer $TOKEN" \
  http://100.x.y.z:8765/healthz
```

Stage and dry-run raw ChatGPT import:

```bash
scripts/ingest_chatgpt_canonical.sh /path/to/chatgpt-export
```

Mine for real only after reviewing the dry run:

```bash
scripts/ingest_chatgpt_canonical.sh /path/to/chatgpt-export --apply --allow-existing-palace
```

`scripts/ingest_chatgpt_canonical.sh` mines only the raw `chatgpt` exchange
wing by default. The legacy `chatgpt_signals` pass uses local heuristics, not
LocalAI, and only runs with `--allow-legacy-signals`.

Run the LocalAI-derived classification pass with:

```bash
/media/u0/OneDrive_Backup/mempalace/venv/bin/python \
  /media/u0/OneDrive_Backup/mempalace/app/scripts/localai_chatgpt_signals.py \
  --source-dir /media/u0/OneDrive_Backup/mempalace/sources/chatgpt \
  --checkpoint /media/u0/OneDrive_Backup/mempalace/data/localai_chatgpt_signals.checkpoint.jsonl \
  --wing chatgpt_signals \
  --model qwen3-vl-8b-instruct
```

The script reads `secrets/http_token` for MemPalace HTTP MCP and
`secrets/localai_token` for LocalAI. It aborts if LocalAI is unreachable, the
model does not return valid JSON, or the configured LocalAI base URL points at a
cloud endpoint. The intended LLM is LocalAI hosted on `snow-white-iii`; this
deployment should not send ChatGPT exports to cloud APIs.

## ChatGPT signal ontology runner

The ontology runner is intended to run on `snow-white-iii` as the `mempalace`
service user. Keep every path anchored under the canonical palace root:

```text
/media/u0/OneDrive_Backup/mempalace/
  app/
  venv/
  data/ontology/
  secrets/localai_token
```

Do not point the runner at `/media/u0/Extreme SSD`.

LocalAI for this runner is the host-local service at
`http://snow-white-iii:8080/v1`, with token material read from
`/media/u0/OneDrive_Backup/mempalace/secrets/localai_token`. It is not a cloud
endpoint.

The safe default is to generate the ontology run artifacts, including
`apply_ready_manifest.json`, without copying drawers. Materializing copies
requires the explicit apply flag.

The deployed app tree on `snow-white-iii` is a staged copy, not a git checkout.
Do not expect `git pull --ff-only` to work under
`/media/u0/OneDrive_Backup/mempalace/app`. To update the app from a workstation,
stage a clean committed tree under `/media/u0/OneDrive_Backup/tmp-mempalace`,
then promote it locally on `snow-white-iii`:

```bash
scripts/systemd/promote_snow_white_iii_app_update.sh \
  --stage /media/u0/OneDrive_Backup/tmp-mempalace/<staged-app>/app
```

The promotion script copies only into the canonical app directory, never uses
`rsync --delete`, does not touch palace data or secrets, and does not restart
services.

Start the runner with the bounded transient unit wrapper:

```bash
scripts/systemd/start_ontology_runner_snow_white_iii.sh
```

The wrapper starts `mempalace ontology chatgpt-signals --no-dry-run --run` as the
`mempalace` service user and keeps the same service limits used by the HTTP MCP
service:

```text
MemoryMax=16G
CPUQuota=200%
```

The wrapper also defaults to no drawer-copy materialization. Use
`--apply-copies` only after inspecting `apply_ready_manifest.json`.

## Thread-aware ChatGPT signal rebuild

This wrapper runs the LocalAI-backed thread signal extractor on
`snow-white-iii` as the `mempalace` service user and keeps the same bounded
resource profile:

```text
MemoryMax=16G
CPUQuota=200%
Nice=10
IOSchedulingClass=best-effort
IOSchedulingPriority=7
```

LocalAI is the host-local service at `http://snow-white-iii:8080/v1`; no cloud
LLM is used for this pass. The wrapper writes under:

```text
/media/u0/OneDrive_Backup/mempalace/data/localai_chatgpt_thread_signals/
```

Smoke run:

```bash
scripts/systemd/start_chatgpt_thread_signal_rebuild_snow_white_iii.sh --limit 50 --publish --publish-limit 2
```

Full run with explicit publish:

```bash
scripts/systemd/start_chatgpt_thread_signal_rebuild_snow_white_iii.sh --publish
```

Resume or inspect an existing run directory with `--run-dir PATH`. The wrapper
prints the unit name, run directory, progress path, checkpoint/artifact paths,
the publish limit, the MCP publish timeout, and the `journalctl -fu ...` follow
command after launch. The default MemPalace HTTP MCP timeout is `300` seconds because Chroma
embedding/index writes on the hosted palace can exceed a short client timeout.
Override it with `--mcp-timeout N` if needed. Use `--publish-limit N` for
bounded smoke runs; omit it for a full publish.

The script only publishes when `--publish` is present. It does not delete or
rewrite palace data, does not restart services, and refuses any path under
`/media/u0/Extreme SSD`.

## MemPalace dashboard service

The dashboard is a separate service and should be deployed only when it will not
compete with active mining or LocalAI classification. If those workflows are
running, delay the deployment or keep the dashboard in telemetry-only mode; do
not expect search, taxonomy, or drawer browsing until the system is idle.

Default layout:

```text
/media/u0/OneDrive_Backup/mempalace/
  app/
  venv/
  cache/
  logs/
  tmp/
  mempalace-dashboard.env
  secrets/http_token
  secrets/dashboard_token
  secrets/localai_token
```

Files:

- `scripts/systemd/deploy_dashboard_snow_white_iii.sh`
- `scripts/systemd/mempalace-dashboard-run`
- `scripts/systemd/mempalace-dashboard.service`

Deploy from a workstation with root SSH access to `snow-white-iii`:

```bash
scripts/systemd/deploy_dashboard_snow_white_iii.sh
```

The deploy script stages only dashboard runtime files into the canonical app
directory. It does not rsync the whole repo, does not use `--delete`, and does
not restart or reload `mempalace-http.service`, mining services, or LocalAI.
Use `--no-start` to install the unit without starting it.

For the end-user manual, see
`docs/manuals/mempalace_dashboard_end_user_manual_2026-05-04.md`.

The dashboard's ontology progress panel is read-only. It reads
`progress.json`, `artifacts_index.json`, and bounded artifact previews from
`/media/u0/OneDrive_Backup/mempalace/data/ontology/<run_id>/`, and it should
not be used as a write path.

Suggested environment file contents:

```bash
MEMPALACE_DASHBOARD_HOST=100.x.y.z
MEMPALACE_DASHBOARD_PORT=8766
MEMPALACE_DASHBOARD_APP=mempalace.dashboard_server:app
MEMPALACE_DASHBOARD_TOKEN_FILE=/media/u0/OneDrive_Backup/mempalace/secrets/dashboard_token
MEMPALACE_DASHBOARD_MCP_TOKEN_FILE=/media/u0/OneDrive_Backup/mempalace/secrets/http_token
LOCALAI_BASE_URL=http://snow-white-iii:8080/v1
LOCALAI_TOKEN_FILE=/media/u0/OneDrive_Backup/mempalace/secrets/localai_token
LOCALAI_SIGNAL_CHECKPOINT=/media/u0/OneDrive_Backup/mempalace/data/localai_chatgpt_signals.checkpoint.jsonl
```

The service runs as `mempalace:mempalace`, binds only to the Tailscale IPv4
address set in `MEMPALACE_DASHBOARD_HOST`, and keeps token material in
root-owned files readable by `mempalace`. `dashboard_token` protects the browser
dashboard itself; `http_token` is a separate bearer token used only for the
dashboard's upstream HTTP MCP calls. The wrapper defaults those paths to
`secrets/dashboard_token` and `secrets/http_token` and refuses to start if they
resolve to the same secret. The optional LocalAI envs above only affect
read-only `/api/overview` telemetry and should stay on localhost/LAN/tailnet.
The wrapper refuses `/media/u0/Extreme SSD` and does not touch
`mempalace-http.service`, mining services, or LocalAI.

Resource controls for the dashboard are intentionally smaller than the HTTP MCP
service:

```text
MemoryMax=8G
CPUQuota=100%
Nice=15
```
