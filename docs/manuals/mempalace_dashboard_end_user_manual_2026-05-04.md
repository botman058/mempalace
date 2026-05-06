# MemPalace Dashboard End-User Manual

Audience: people using the hosted MemPalace dashboard on the tailnet.

Current deployment:

```text
Host: snow-white-iii
URL:  http://100.112.179.49:8766/
Mode: read-only dashboard
```

The dashboard is for viewing MemPalace state and searching memories. It is not
an admin console. It cannot delete drawers, edit memories, start mining, restart
services, or rebuild indexes.

The ontology progress panel is also read-only. It shows run state from
`progress.json`, `artifacts_index.json`, and bounded previews under
`/media/u0/OneDrive_Backup/mempalace/data/ontology/<run_id>/`. It does not
trigger ontology writes or semantic copies.

## Quick Start

1. Open the dashboard URL:

   ```text
   http://100.112.179.49:8766/
   ```

2. Get the dashboard token:

   ```bash
   ssh root@snow-white-iii 'cat /media/u0/OneDrive_Backup/mempalace/secrets/dashboard_token'
   ```

3. Paste the token into **Bearer token**.

4. Leave **API base** blank.

5. Select **Save**.

The dashboard page loads before you enter a token, but it does not fetch any
dashboard data until a token is saved.

## What You Can Do

- Check whether the hosted palace is reachable.
- See the current drawer count.
- Confirm whether embeddings are using CUDA.
- See whether mining or LocalAI classification is active.
- See bounded LocalAI and checkpoint telemetry.
- Browse wings, rooms, and drawers when mining is idle.
- Run hybrid search when mining is idle.
- Inspect drawer text and metadata when mining is idle.

## What You Cannot Do

- Delete drawers.
- Edit drawers.
- Start or stop mining.
- Restart MemPalace services.
- Restart LocalAI.
- Rebuild Chroma indexes.
- Change the palace.
- Send export text to cloud APIs.

## Reading the Overview

The top of the dashboard has four main cards:

- **Service health**: whether the dashboard can reach the hosted MemPalace HTTP
  service.
- **Drawer count**: how many drawers the hosted palace currently reports.
- **Embedding device**: the effective embedding device, usually `cuda` on
  `snow-white-iii`.
- **Mining state**: whether the dashboard is in idle mode or telemetry-only
  mode.

The telemetry strip shows:

- **LocalAI**: whether LocalAI on `snow-white-iii` is reachable.
- **Checkpoint**: whether the LocalAI classification checkpoint is readable.
- **Last refresh**: when the browser last refreshed dashboard state.
- **Connection**: whether the browser is connected to the dashboard backend.

## Telemetry-Only Mode

If `mempalace-localai-chatgpt-signals.service` or a mining process is active,
the dashboard switches to telemetry-only mode.

Operators can also force telemetry-only mode with:

```bash
MEMPALACE_DASHBOARD_FORCE_TELEMETRY_ONLY=1
```

Use forced mode during ChatGPT thread-signal rebuilds (`localai_chatgpt_thread_signals.py`)
to prevent dashboard heavy reads from competing with rebuild CPU/IO.

This is expected. In telemetry-only mode, the dashboard does not run heavy
Chroma-backed reads. That protects the active mining/classification job.

Available in telemetry-only mode:

- overview cards
- LocalAI telemetry
- checkpoint telemetry
- mining-state details
- ontology progress runs and dashboard-safe ontology artifact previews

Disabled in telemetry-only mode:

- search
- taxonomy browsing
- drawer list
- drawer detail

If you try a heavy read while telemetry-only mode is active, the API returns:

```text
423 Locked
```

That is a safety feature, not a failure.

## Search

Search works only when **Mining state** is `Idle`.

1. Type a short query in **Hybrid search**.
2. Optionally choose a wing and room.
3. Select **Search**.
4. Select a result to view its details.

Search uses the hosted MemPalace HTTP MCP service on `snow-white-iii`. Your
client machine does not open a local palace or run local embeddings.

## Taxonomy Browser

The taxonomy browser works only when **Mining state** is `Idle`.

- A **wing** is a high-level source or entity grouping.
- A **room** is a topic or sub-group inside a wing.
- A **drawer** is a stored memory chunk.

Select a taxonomy tile to set the wing filter. The drawer browser will update
to that scope.

## Drawer Browser

The drawer browser works only when **Mining state** is `Idle`.

- The left side lists drawers for the current wing/room filters.
- Selecting a drawer opens the detail panel.
- The detail panel shows text and metadata returned by the hosted palace.

If the browser looks empty, clear the wing and room filters.

## Troubleshooting

| Symptom | Meaning | Fix |
|---|---|---|
| Page loads, but everything says token required | No dashboard token is saved in the browser. | Paste the dashboard token and select **Save**. |
| `401 Unauthorized` | The request did not include a token. | Re-enter the dashboard token. |
| `403 Forbidden` | The token is wrong. | Re-read `secrets/dashboard_token`. |
| `423 Locked` | Mining or LocalAI classification is active. | Wait; this protects the active job. |
| `423 Locked` while system looks idle | Forced telemetry-only mode is enabled. | Verify `MEMPALACE_DASHBOARD_FORCE_TELEMETRY_ONLY`; set to `0` when rebuild is complete. |
| `upstream_unavailable` | Dashboard cannot reach the hosted HTTP MCP service. | Check `mempalace-http.service` on `snow-white-iii`. |
| LocalAI says unavailable | LocalAI telemetry failed. | Check LocalAI on `snow-white-iii`; dashboard search may still work when idle. |
| Checkpoint says unavailable | The checkpoint path is missing or unreadable. | Check `/media/u0/OneDrive_Backup/mempalace/data/localai_chatgpt_signals.checkpoint.jsonl`. |

## Operator Commands

Check service state:

```bash
ssh root@snow-white-iii 'systemctl is-active mempalace-dashboard.service'
ssh root@snow-white-iii 'systemctl is-active mempalace-http.service'
ssh root@snow-white-iii 'systemctl is-active mempalace-localai-chatgpt-signals.service'
```

View recent dashboard logs:

```bash
ssh root@snow-white-iii 'journalctl -u mempalace-dashboard.service -n 80 --no-pager'
```

Redeploy the dashboard from this repository:

```bash
scripts/systemd/deploy_dashboard_snow_white_iii.sh
```

The deploy helper stages only dashboard runtime files and installs/starts only
`mempalace-dashboard.service`. It does not restart `mempalace-http.service`,
LocalAI, mining services, or touch palace data/checkpoints.

## Safety Model

The dashboard has two separate tokens:

- `secrets/dashboard_token`: used by the browser to access the dashboard.
- `secrets/http_token`: used by the dashboard backend to call hosted MemPalace
  HTTP MCP.

The dashboard backend only calls read-only MCP tools:

- `mempalace_get_taxonomy`
- `mempalace_search`
- `mempalace_list_drawers`
- `mempalace_get_drawer`

When mining/classification is active, even those read-only tools are blocked for
search/browsing and the dashboard stays in telemetry-only mode.
