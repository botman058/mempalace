# MemPalace HTTP MCP Closure Worksheet

Date: 2026-05-03
Owner: O-0
Branch target: `codex/mempalace-http-mcp-closure`
Fork push target: `git@github.com:botman058/mempalace.git`

## Control Plane

- O-0 owns final orchestration, verification evidence, documentation truth, commit, and direct fork push.
- Keep `origin` as `git@github.com:MemPalace/mempalace.git`.
- Do not commit on `develop`; use `codex/mempalace-http-mcp-closure`.
- Stage only scoped HTTP MCP hosting files, ChatGPT room-boundary fixes, tests, docs, and this worksheet.
- Exclude unrelated dirty files from commit: `.agents/plugins/marketplace.json`.
- Preserve all remote non-empty palace/source/cache data. No remote deletion is authorized in this work package.
- Local cleanup is authorized only for prior black-hole-iii MemPalace runtime artifacts after the hosted client path verifies: `/home/u4/.mempalace`, `/home/u4/repos/mempalace/.venv`, and obsolete local symlink backups under `/home/u4/.local/bin`.
- Do not use `/media/u0/Extreme SSD`.
- Do not change CUDA drivers, system CUDA, or global Python packages.
- Remote service must remain Tailnet-bound and bearer-token protected.
- LLM classification must route through LocalAI on `snow-white-iii` only. Cloud endpoints such as `https://api.openai.com/v1` are out of scope for this deployment.

## Preserved Baseline

- Repository: `/home/u4/repos/mempalace`
- Baseline branch: `develop`
- Baseline HEAD: `1888b67`
- Branch relation at worksheet creation: `develop...origin/develop` is `0 ahead / 0 behind`.
- Current `origin`: `git@github.com:MemPalace/mempalace.git` for fetch and push.
- Target remote service host: `snow-white-iii`
- Target service address: `100.112.179.49:8765`
- Target remote app path: `/media/u0/OneDrive_Backup/mempalace/app`
- Target remote data path: `/media/u0/OneDrive_Backup/mempalace/data`

## Checkpoints

### Checkpoint A - Worksheet Preserved

Required evidence:

- `docs/worksheets/mempalace_http_mcp_closure_worksheet_2026-05-03.md` exists and records current repo/remote truth.

Disposition: green.

### Checkpoint B - Scope Clean

Required evidence:

- Branch is `codex/mempalace-http-mcp-closure`.
- `git status -sb` reviewed before staging.
- Explicit scoped file list excludes `.agents/plugins/marketplace.json`.
- Direct dry-run push to `git@github.com:botman058/mempalace.git` still succeeds.

Disposition: green.

### Checkpoint C - Remote Reconciled

Required evidence:

- Final scoped files deployed to `/media/u0/OneDrive_Backup/mempalace/app`.
- `mempalace-http.service` restarted.
- Running service is using the redeployed code.
- No remote data deletion is performed.

Disposition: green.

### Checkpoint D - Verification Green

Required evidence:

- Ruff passes.
- Python compile check passes.
- Bash syntax check passes for systemd scripts.
- Targeted pytest suite passes.
- Remote `pip check` passes.
- Remote ONNX Runtime providers include `CUDAExecutionProvider`.
- Remote unauthenticated health check returns `401`.
- Remote authenticated `/healthz` reports `effective_embedding_device=cuda`.
- Remote service bounds show `MemoryMax=16G` and `CPUQuota=200%`.

Disposition: green.

### Checkpoint E - Fork Push Complete

Required evidence:

- One scoped commit hash exists on `codex/mempalace-http-mcp-closure`.
- `git push git@github.com:botman058/mempalace.git HEAD:refs/heads/codex/mempalace-http-mcp-closure` succeeds.
- Final `git status -sb` shows only unrelated pre-existing dirty files if any.

Disposition: green.

## Work Packages

### WP-00 - Materialize Closure Worksheet

Owner: O-0
Status: complete

Deliverable: this worksheet file.

### WP-01 - Branch and Scope Hygiene

Owner: O-0
Status: complete

Deliverable: safe closure branch and exact staging plan.

### WP-02 - Remote Deployment Reconciliation and Cleanup

Owner: O-0
Status: complete

Deliverable: remote app files reconciled and service restarted without remote data deletion.

### WP-03 - Verification Sweep

Owner: O-0
Status: complete

Deliverable: local and remote command evidence for closure checks.

### WP-04 - Documentation, Devlog, and Handoff Truth

Owner: O-0
Status: complete

Deliverable: docs and worksheet accurately describe implemented behavior, LocalAI-only classification constraints, hybrid search, and caveats.

### WP-05 - Commit and Push to Fork

Owner: O-0
Status: complete

Deliverable: one scoped commit pushed directly to the fork URL.

## Scoped Files

Final intended scope, subject to O-0 reread before staging:

- `CHANGELOG.md`
- `examples/mcp_setup.md`
- `mempalace/cli.py`
- `mempalace/convo_miner.py`
- `mempalace/http_client.py`
- `mempalace/http_mcp_server.py`
- `mempalace/http_stdio_proxy.py`
- `mempalace/mcp_server.py`
- `mempalace/normalize.py`
- `pyproject.toml`
- `scripts/ingest_chatgpt_canonical.sh`
- `scripts/localai_chatgpt_signals.py`
- `scripts/systemd/install_snow_white_iii.sh`
- `scripts/systemd/mempalace-http-run`
- `scripts/systemd/mempalace-http.service`
- `scripts/systemd/mempalace.env.template`
- `scripts/systemd/README.md`
- `tests/test_http_client.py`
- `tests/test_http_mcp_server.py`
- `tests/test_mcp_server.py`
- `tests/test_convo_miner.py`
- `tests/test_normalize.py`
- `website/guide/mcp-integration.md`
- `docs/worksheets/mempalace_http_mcp_closure_worksheet_2026-05-03.md`

Explicitly excluded from staging:

- `.agents/plugins/marketplace.json`

## Evidence Log

### 2026-05-03 - WP-00 Baseline Commands

- `git -C /home/u4/repos/mempalace status -sb` showed branch `develop...origin/develop` with dirty scoped HTTP MCP files plus unrelated dirty `.agents/plugins/marketplace.json`, `mempalace/normalize.py`, and `tests/test_normalize.py`.
- `git -C /home/u4/repos/mempalace rev-parse --short HEAD` returned `1888b67`.
- `git -C /home/u4/repos/mempalace rev-list --left-right --count develop...origin/develop` returned `0 0`.
- `git -C /home/u4/repos/mempalace remote -v` showed `origin` fetch/push as `git@github.com:MemPalace/mempalace.git`.
- `test -f docs/worksheets/mempalace_http_mcp_closure_worksheet_2026-05-03.md` exited successfully.

### 2026-05-03 - WP-01 Branch and Scope Hygiene

- `git switch -c codex/mempalace-http-mcp-closure` created and switched to the closure branch.
- `git status -sb` showed branch `codex/mempalace-http-mcp-closure` with scoped HTTP MCP files plus dirty `.agents/plugins/marketplace.json`, `mempalace/normalize.py`, and `tests/test_normalize.py`. After the ChatGPT privacy-export investigation, `mempalace/normalize.py` and `tests/test_normalize.py` were moved into scope.
- `git diff --name-only` confirmed tracked dirty files include unrelated excluded files and scoped files; staging will use the explicit `Scoped Files` list only.
- `git ls-files --others --exclude-standard` showed untracked scoped HTTP MCP files, systemd scripts, tests, and this worksheet.
- `git push --dry-run git@github.com:botman058/mempalace.git HEAD:refs/heads/codex/mempalace-http-mcp-closure` succeeded and would create the branch on the fork.

### 2026-05-03 - Parser and Bridge Findings

- Explorer Lagrange confirmed the ChatGPT room-collapse failure: `normalize()` flattened privacy-export conversation lists into one transcript, and `mine_convos()` assigned one room to the whole file. The fix scope is `normalize.py`, `convo_miner.py`, `tests/test_normalize.py`, and `tests/test_convo_miner.py`.
- Explorer Aristotle confirmed the LocalAI-only bridge boundary: exocortex should export one normalized transcript file per conversation plus optional `exocortex_rollup_v3` sidecar; MemPalace should mine that narrow stage rather than consuming archivekg's full SQLite schema.
- Bridge preflight must fail closed unless `ARCHIVEKG_LLM_REMOTE=1`, an OpenAI-compatible LocalAI base URL is configured on `snow-white-iii`, and the base URL is not a cloud endpoint such as `https://api.openai.com/v1`.

### 2026-05-03 - WP-02 Remote Reconciliation

- `rsync -a --exclude .git --exclude .venv --exclude .pytest_cache /home/u4/repos/mempalace/ root@snow-white-iii:/media/u0/OneDrive_Backup/mempalace/app/` deployed app files without `--delete`.
- Remote install copied only the staged `mempalace-http-run` and `mempalace-http.service`, then ran `systemctl daemon-reload` and restarted `mempalace-http.service`.
- `systemctl show mempalace-http.service` reported `ActiveState=active`, `SubState=running`, `CPUQuotaPerSecUSec=2s`, and `MemoryMax=17179869184`.
- `systemctl cat mempalace-http.service` showed `CPUQuota=200%`.
- No remote source, cache, tmp, or palace data deletion was performed.

### 2026-05-03 - WP-03 Verification Sweep

- `.venv/bin/python -m ruff check ...` passed on the changed Python modules and tests.
- `.venv/bin/python -m py_compile ...` passed for the changed Python modules.
- `bash -n scripts/systemd/install_snow_white_iii.sh scripts/systemd/mempalace-http-run scripts/ingest_chatgpt_canonical.sh` passed.
- `.venv/bin/python -m pytest tests/test_normalize.py tests/test_convo_miner.py tests/test_mcp_server.py tests/test_http_client.py tests/test_http_mcp_server.py tests/test_hybrid_candidate_union.py -q` passed: `220 passed in 152.64s`.
- Remote `runuser -u mempalace -- /media/u0/OneDrive_Backup/mempalace/venv/bin/python -m pip check` returned `No broken requirements found.`
- Remote ONNX Runtime providers were `['TensorrtExecutionProvider', 'CUDAExecutionProvider', 'CPUExecutionProvider']`.
- Local unauthenticated `GET http://100.112.179.49:8765/healthz` returned `401`.
- Authenticated `/healthz` returned `configured_embedding_device=cuda`, `effective_embedding_device=cuda`, and `drawer_count=0`.
- `git diff --check` returned clean.

### 2026-05-03 - Thin Client and Cleanup

- `/home/u4/.local/bin/mempalace` and `/home/u4/.local/bin/mempalace-mcp` were replaced with self-contained stdlib HTTP clients defaulting to `http://100.112.179.49:8765`.
- `/home/u4/.config/mempalace/http_token` was installed with mode `0600`; the token value was not printed.
- `mempalace health`, `mempalace status`, and a stdio MCP `initialize` request through `mempalace-mcp` all succeeded against `snow-white-iii`.
- Removed old local runtime artifacts after hosted client verification: `/home/u4/.mempalace`, `/home/u4/repos/mempalace/.venv`, `/home/u4/.local/bin/mempalace.symlink-20260503-145618`, and `/home/u4/.local/bin/mempalace-mcp.symlink-20260503-145618`.
- Verified `/home/u4/.mempalace` and `/home/u4/repos/mempalace/.venv` are absent, while `/home/u4/repos/mempalace` remains.

### 2026-05-03 - WP-05 Fork Push

- `git commit -m "Host MemPalace over tailnet HTTP MCP"` created the scoped closure commit.
- `git push git@github.com:botman058/mempalace.git HEAD:refs/heads/codex/mempalace-http-mcp-closure` succeeded and created the fork branch.

### 2026-05-03 - Remote Re-Mining and LocalAI Pass

- Raw ChatGPT mining was restarted on `snow-white-iii` as
  `mempalace-mine-chatgpt.service` with `User=mempalace`,
  `CPUQuota=200%`, `MemoryMax=16G`, and
  `MEMPALACE_EMBEDDING_DEVICE=cuda`.
- The initial raw mining attempt failed before writing embeddings because the
  transient unit lacked the venv CUDA/cuDNN `LD_LIBRARY_PATH`; the fixed unit
  uses the same CUDA library path as `mempalace-http.service`.
- CUDA was proven under `User=mempalace` by embedding a probe sentence with
  `MEMPALACE_EMBEDDING_DEVICE=cuda`, returning `device cuda` and
  `embedding_dims 384`.
- `scripts/localai_chatgpt_signals.py` was added as a fail-closed LocalAI
  classification bridge. It parses ChatGPT `conversations.json`, calls
  `http://snow-white-iii:8080/v1/chat/completions`, refuses
  `api.openai.com`, and files classified signal drawers through
  `mempalace_add_drawer` in the HTTP MCP service.
- Remote secrets were staged under
  `/media/u0/OneDrive_Backup/mempalace/secrets/` as `root:mempalace` with mode
  `0640`; token values were not printed.
- `mempalace-localai-chatgpt-signals.service` was queued as `User=mempalace`
  with `CPUQuota=200%` and `MemoryMax=16G`. It waits for
  `mempalace-mine-chatgpt.service` to stop before starting the LocalAI pass, so
  raw embedding and LLM classification do not compete for the GPU at the same
  time.
- Raw mining completed successfully at `2026-05-03T19:10:35-04:00`: 19
  `conversations.json` files processed, 135,182 raw `chatgpt` drawers filed,
  and peak memory was 3.7G.
- After the raw mine stopped, `mempalace-localai-chatgpt-signals.service`
  started `scripts/localai_chatgpt_signals.py` as `mempalace`. The first
  checkpoint recorded one classified conversation and six filed
  `chatgpt_signals` drawers, with the HTTP service remaining healthy.
