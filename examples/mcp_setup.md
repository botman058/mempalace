# MCP Integration — Claude Code

## Setup

Run the MCP server:

```bash
mempalace-mcp
```

Or add it to Claude Code:

```bash
claude mcp add mempalace -- mempalace-mcp
```

## HTTP MCP

MemPalace can also serve MCP over token-protected HTTP:

```bash
export MEMPALACE_PALACE_PATH=/media/u0/OneDrive_Backup/mempalace/data/palace
export MEMPALACE_HTTP_HOST=100.x.y.z
export MEMPALACE_HTTP_PORT=8765
export MEMPALACE_HTTP_TOKEN_FILE=/media/u0/OneDrive_Backup/mempalace/secrets/http_token
mempalace-mcp-http --host "$MEMPALACE_HTTP_HOST" --port "$MEMPALACE_HTTP_PORT"
```

The HTTP endpoint is `POST /mcp`; health is `GET /healthz`. Both require
`Authorization: Bearer <token>` unless `MEMPALACE_HTTP_ALLOW_NO_AUTH=1` is set
for isolated local development.

On a client machine, point CLI and stdio MCP calls at the remote endpoint:

```bash
export MEMPALACE_HTTP_URL=http://100.112.179.49:8765
export MEMPALACE_HTTP_TOKEN_FILE=/path/to/http_token
mempalace status
mempalace search "query"
claude mcp add mempalace -- mempalace-mcp
```

Set `MEMPALACE_LOCAL=1` or pass `--palace` to force local palace access.
Hosted search uses the MCP server's hybrid retrieval path: vector candidates
and BM25 candidates are merged, then re-ranked before results are returned.

## Available Tools

The server exposes the full MemPalace MCP toolset. Common entry points include:

- **mempalace_status** — palace stats (wings, rooms, drawer counts)
- **mempalace_search** — semantic search across all memories
- **mempalace_list_wings** — list all projects in the palace

## Usage in Claude Code

Once configured, Claude Code can search your memories directly during conversations.
