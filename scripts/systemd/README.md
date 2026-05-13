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

If a prior run checkpointed transient LocalAI failures as `status: error`, use
safe resume mode to retry only those segments:

```bash
scripts/systemd/start_chatgpt_thread_signal_rebuild_snow_white_iii.sh \
  --run-dir /media/u0/OneDrive_Backup/mempalace/data/localai_chatgpt_thread_signals/<run_id> \
  --retry-errors \
  --provider-max-attempts 2
```

Default resume behavior still skips already checkpointed `classified` and
`invalid_output` segments, so recovered work is not reclassified or duplicated.
Malformed/truncated `conversations.json` files are now recorded into durable run
artifacts (`source_file_errors.jsonl`, `source_checkpoint.jsonl`) and skipped so
the rest of the rebuild can continue.

The script only publishes when `--publish` is present. It does not delete or
rewrite palace data, does not restart services, and refuses any path under
`/media/u0/Extreme SSD`.

## Atlas-guided ChatGPT extraction (WP-05 no-publish pass)

This wrapper runs the atlas-guided LocalAI extraction pass on
`snow-white-iii` as the `mempalace` service user with bounded resources:

```text
MemoryMax=16G
CPUQuota=200%
Nice=10
IOSchedulingClass=best-effort
IOSchedulingPriority=7
```

Canonical defaults:

```text
ROOT              /media/u0/OneDrive_Backup/mempalace
SOURCE            /media/u0/OneDrive_Backup/mempalace/sources/chatgpt
ATLAS RUN         /media/u0/OneDrive_Backup/mempalace/data/chatgpt_archive_atlas/atlas_full2_20260512T0412Z_2fc8ac5
GUIDED RUN ROOT   /media/u0/OneDrive_Backup/mempalace/data/atlas_guided_chatgpt_signals
LOCALAI           http://snow-white-iii:8080/v1
TOKEN FILE        /media/u0/OneDrive_Backup/mempalace/secrets/localai_token
```

Run a bounded smoke pass:

```bash
scripts/systemd/start_chatgpt_atlas_guided_extraction_snow_white_iii.sh \
  --run-id atlas_guided_smoke_20260512 \
  --limit 25 \
  --provider-max-attempts 2
```

Resume an existing guided run directory and retry only prior provider errors:

```bash
scripts/systemd/start_chatgpt_atlas_guided_extraction_snow_white_iii.sh \
  --run-dir /media/u0/OneDrive_Backup/mempalace/data/atlas_guided_chatgpt_signals/<run_id> \
  --retry-errors \
  --provider-max-attempts 2
```

Use a different atlas artifact set under the canonical atlas root:

```bash
scripts/systemd/start_chatgpt_atlas_guided_extraction_snow_white_iii.sh \
  --atlas-run-dir /media/u0/OneDrive_Backup/mempalace/data/chatgpt_archive_atlas/<atlas_run_id> \
  --candidate-records /media/u0/OneDrive_Backup/mempalace/data/chatgpt_archive_atlas/<atlas_run_id>/candidate_bridge_records.jsonl
```

The wrapper always passes `--atlas-guided`, always supplies the host-local
LocalAI URL and token file, and never passes `--publish`. It rejects non-local
provider URLs, rejects non-canonical token paths, refuses `/media/u0/Extreme SSD`,
and aborts on non-`snow-white-iii` hosts unless `MEMPALACE_INSTALL_ALLOW_OTHER_HOST=1`
is explicitly set in the existing wrapper style.

Before submitting the transient unit it verifies the expected atlas inputs are
present under the selected atlas run directory:

```text
candidate_bridge_records.jsonl
atlas_thread_candidates.jsonl
atlas_candidate_coverage.json
thread_index.jsonl
```

The unit writes only under the selected guided run directory and leaves palace
drawers untouched. After launch it prints the transient unit name plus the
progress and artifact paths:

```text
progress.json
extraction_records.jsonl
invalid_outputs.jsonl
reconciled_signals.jsonl
publish_checkpoint.jsonl
```

## ChatGPT archive atlas runner (pre-LLM, artifact-only)

This wrapper runs the pre-LLM ChatGPT archive atlas pass on `snow-white-iii`
as the `mempalace` service user with bounded resources:

```text
MemoryMax=16G
CPUQuota=200%
```

Canonical defaults:

```text
ROOT      /media/u0/OneDrive_Backup/mempalace
SOURCE    /media/u0/OneDrive_Backup/mempalace/sources/chatgpt
RUN ROOT  /media/u0/OneDrive_Backup/mempalace/data/chatgpt_archive_atlas
APP       /media/u0/OneDrive_Backup/mempalace/app
```

Start a bounded smoke run:

```bash
scripts/systemd/start_chatgpt_archive_atlas_snow_white_iii.sh --limit 50
```

Start a full run with explicit run id:

```bash
scripts/systemd/start_chatgpt_archive_atlas_snow_white_iii.sh \
  --run-id atlas_full_20260510 \
  --run-root /media/u0/OneDrive_Backup/mempalace/data/chatgpt_archive_atlas \
  --source-dir /media/u0/OneDrive_Backup/mempalace/sources/chatgpt
```

This wrapper is pre-LLM and artifact-only: no LocalAI dependency, no cloud
LLM calls, no MCP write/publish flags. It does not delete files, does not
restart services, and refuses any path under `/media/u0/Extreme SSD`.

The runner writes only under the selected atlas run directory. It materializes
phase artifacts progressively for inspection during a run:

```text
progress.json
source_file_errors.jsonl
conversation_index.jsonl
thread_index.jsonl
lexical_sketches.jsonl
thread_embeddings.jsonl
thread_embedding_vectors.jsonl
topic_clusters.jsonl
atlas_summary.md
atlas_summary_manifest.json
artifacts_index.json
```

`progress.json` is updated after each phase and records `failed` if the runner
errors after the run directory is created. Embedding artifacts are owned by the
embedding cache; the runner does not rewrite them after cache materialization.

The default embedding path is local-only and fail-closed. It requires the
Chroma `all-MiniLM-L6-v2` ONNX files to already be present in the service
user's local cache before the default embedder is constructed. If the local
cache is missing, the runner fails before any Chroma download path is invoked.

Completed full-run reference, 2026-05-12:

```text
Run ID:   atlas_full2_20260512T0412Z_2fc8ac5
Run dir:  /media/u0/OneDrive_Backup/mempalace/data/chatgpt_archive_atlas/atlas_full2_20260512T0412Z_2fc8ac5
Status:   complete
Rows:     4,283 conversations; 4,746 threads; 3,120 topic clusters
Device:   4,746/4,746 embedding rows recorded effective_device=cuda
Runtime:  33min 42.420s CPU time; 4.0G memory peak
```

That run emitted all expected artifact files and passed schema validation. It
remained pre-LLM and artifact-only: no LocalAI call, no cloud LLM call, no MCP
publish, and no palace drawer mutation.

## MemPalace dashboard service

The dashboard is a separate service and should be deployed only when it will not
compete with active mining or LocalAI classification. If those workflows are
running, delay the deployment or keep the dashboard in telemetry-only mode; do
not expect search, taxonomy, or drawer browsing until the system is idle.

During heavy ChatGPT thread-signal rebuilds, set:

```bash
MEMPALACE_DASHBOARD_FORCE_TELEMETRY_ONLY=1
```

This forces telemetry-only mode even if process detection misses a transient
runner/unit. In forced mode the dashboard still serves `/api/overview` and
read-only ontology run progress/artifact endpoints, but search/taxonomy/drawer
endpoints return `423 Locked` without upstream MCP tool calls.

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
MEMPALACE_DASHBOARD_FORCE_TELEMETRY_ONLY=0
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
