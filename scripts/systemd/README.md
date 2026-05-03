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
