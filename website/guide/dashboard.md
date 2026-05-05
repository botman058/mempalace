# Dashboard

The MemPalace dashboard is a read-only browser interface for a hosted palace.
It is meant for checking service health, watching mining progress, browsing the
taxonomy, and running searches when the palace is idle.

The dashboard is not an admin console. It does not delete drawers, start mining,
restart services, rebuild indexes, or edit palace data.

## Open the Dashboard

Your operator will give you a tailnet URL, usually like:

```text
http://100.x.y.z:8766/
```

The page itself can load without a token. Data does not load until you enter a
bearer token.

1. Open the dashboard URL in a browser on a tailnet-connected machine.
2. Paste the dashboard bearer token into **Bearer token**.
3. Leave **API base** empty unless your operator tells you otherwise.
4. Select **Save**.

The token is stored in your browser's local storage. Do not paste the HTTP MCP
token here unless your deployment intentionally uses the same token. The
recommended deployment uses a separate dashboard token.

## What the Overview Shows

The top cards show the current operational state:

- **Service health**: whether the dashboard can reach the hosted MemPalace HTTP
  service.
- **Drawer count**: the current number of indexed drawers reported by the
  hosted palace.
- **Embedding device**: the effective embedding device, such as `cuda`.
- **Mining state**: `Idle` or `Active`.
- **LocalAI**: whether the configured LocalAI endpoint is reachable.
- **Checkpoint**: the latest bounded status from the LocalAI classification
  checkpoint file.

The dashboard reads LocalAI and checkpoint state only for telemetry. It does not
send source text to cloud APIs.

## Telemetry-Only Mode

When mining or LocalAI classification is active, the dashboard switches to
telemetry-only mode.

In telemetry-only mode:

- overview telemetry remains available
- search is disabled
- taxonomy browsing is disabled
- drawer list and drawer detail are disabled
- read-heavy endpoints return `423 Locked`

This is intentional. Search and taxonomy reads can compete with Chroma-backed
mining, so the dashboard refuses those calls until the mining guard reports
idle.

## Search When Idle

Search is available only when **Mining state** is `Idle`.

1. Enter a short query in **Hybrid search**.
2. Optionally select a wing and room.
3. Select **Search**.
4. Select a result to inspect its drawer text and metadata.

Dashboard search uses the hosted MemPalace HTTP MCP read-only search tool. It
does not open a local palace on your client machine.

## Browse Taxonomy and Drawers

When the palace is idle:

- **Taxonomy browser** lists wings and their room counts.
- Selecting a taxonomy tile sets the wing filter.
- **Drawer browser** lists drawers for the selected scope.
- Selecting a drawer opens the drawer detail panel.

If no rooms or drawers appear, clear the wing/room filters and try again.

## Ontology Progress

The dashboard backend also exposes read-only ontology run endpoints for the
progress panel:

- `GET /api/ontology/runs`
- `GET /api/ontology/runs/{run_id}`
- `GET /api/ontology/runs/{run_id}/artifacts`
- `GET /api/ontology/runs/{run_id}/unresolved-preview`

These endpoints read the run directory directly from the ontology run root and
do not call Chroma, LocalAI, or the MCP mutation tools. They remain available
while mining or classification is active so operators can inspect live progress
without waiting for the run to finish.

## Common States

| State | Meaning | What to do |
|---|---|---|
| `Token required` | The browser has not sent a bearer token yet. | Paste the dashboard token and select **Save**. |
| `401 Unauthorized` | Missing token. | Re-enter the dashboard token. |
| `403 Forbidden` | Wrong token. | Ask the operator for the dashboard token. |
| `423 Locked` | Mining or classification is active. | Wait for the active job to finish. |
| `upstream_unavailable` | Dashboard cannot reach HTTP MCP. | Ask the operator to check `mempalace-http.service`. |
| `LocalAI not_configured` | LocalAI telemetry env vars are absent. | Search may still work when idle; ask the operator if LocalAI telemetry is expected. |

## Operator Notes

The snow-white-iii deployment helper is:

```bash
scripts/systemd/deploy_dashboard_snow_white_iii.sh
```

It stages only dashboard runtime files, creates `secrets/dashboard_token` if
missing, uses `secrets/http_token` for upstream HTTP MCP, and starts only
`mempalace-dashboard.service`.

The dashboard service should remain separate from `mempalace-http.service`.
Do not deploy it by restarting mining, LocalAI, or the hosted HTTP MCP service.
