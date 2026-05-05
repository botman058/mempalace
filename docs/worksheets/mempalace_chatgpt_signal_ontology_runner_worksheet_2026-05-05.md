# MemPalace ChatGPT Signal Ontology Runner - Orchestrated Worksheet
Date: 2026-05-05
Repo baseline: `/home/u4/repos/mempalace`
Live branch baseline: `codex/mempalace-http-mcp-closure` at `99e2ae8`
Observed branch relation: local checkout on closure branch; out-of-scope dirty `.agents/plugins/marketplace.json` and unaccepted untracked `docs/reference/` remain present
Document type: implementation worksheet
Objective: turn the completed ontology artifact/prompt tranche into a resumable LocalAI-backed runner that can re-mine `chatgpt_signals` into progressive dashboard-visible ontology artifacts and optionally materialize verified semantic copies without mutating source drawers.

---

## control plane

### Top-level orchestrator

- **Only top-level orchestrator:** `O-0`
- **Model:** `gpt-5.5`
- **Reasoning depth:** `xhigh`
- **Authority:** assign packages, enforce mutation lock, review evidence, integrate accepted patches, update worksheet/devlog/docs, commit, and push milestones
- **Forbidden uses:** direct package implementation, deleting files or palace data, mutating original `chatgpt_signals` drawers, touching `.agents/plugins/marketplace.json`, staging unaccepted `docs/reference/`, using `/media/u0/Extreme SSD`, cloud LLM upload without separate explicit approval
- **Mutation lock:** `O-0` is read/review/orchestrate-only by default. Direct implementation edits are forbidden except in declared worksheet/status, integration, or emergency repair mode.

### Working rule

One continuation worksheet controls this tranche:
`docs/worksheets/mempalace_chatgpt_signal_ontology_runner_worksheet_2026-05-05.md`.

`O-0` rereads this worksheet before package activation, worker acceptance, checkpoint closure, docs/devlog updates, staging, commit, and push.

### Current hard gate

Checkpoint A is green. WP-01 through WP-03 may proceed in non-conflicting worker-owned slices. WP-04 remains blocked until implementation and ops/docs evidence are accepted.

---

## reasoning-depth matrix

| Model | Reasoning depth | Intended uses | Forbidden uses |
|---|---:|---|---|
| `gpt-5.5` | xhigh | `O-0` orchestration, architecture arbitration, checkpoint verdicts, integration | direct package implementation outside declared mutation modes |
| `gpt-5.4` | high | runner architecture, LocalAI/cloud-safety review, MCP/apply safety review | dashboard styling ownership |
| `gpt-5.4-mini` | medium | focused tests, docs, systemd wrappers, dashboard/readme updates | taxonomy or safety arbitration |
| `gpt-5.3-codex` | medium | bounded implementation patches with clear file ownership | independent safety review |
| `gpt-5.3-codex-spark` | medium | narrow syntax/test verification, fixture generation | architecture or mutation-path ownership |

---

## standing constraints

1. Do not delete files or palace data without explicit confirmation.
2. Do not mutate original `chatgpt_signals` drawers.
3. Do not overwrite outside explicitly designated working folders.
4. Canonical run artifacts live under `/media/u0/OneDrive_Backup/mempalace/data/ontology/<run_id>/`.
5. Do not use `/media/u0/Extreme SSD`.
6. LocalAI is hosted on `snow-white-iii`; cloud LLM APIs are forbidden unless the user separately approves a previewed batch.
7. CPU cap target remains 200%; memory cap target remains 16G for services.
8. The dashboard is read-only and must not trigger ontology writes, LocalAI calls, MCP mutations, mining, or source rescans.
9. Semantic copies are optional and must only run from an apply-ready manifest produced after local verification.
10. Use deterministic IDs and resumable phase files so reruns are idempotent.
11. Do not stage or modify `.agents/plugins/marketplace.json`.
12. Do not stage, rewrite, or delete unaccepted `docs/reference/`.
13. Push accepted milestones explicitly to `git@github.com:botman058/mempalace.git HEAD:refs/heads/codex/mempalace-http-mcp-closure`.

---

## O-0 mutation lock

`O-0` is read/review/orchestrate-only until a package has explicit activation, bounded worker ownership, returned implementation evidence, required independent review, and an `O-0` checkpoint verdict.

`O-0` must not directly edit repo files, call `apply_patch`, run write commands, run rewriting formatters, generate migrations/codegen, stage commits, or push during package implementation.

Allowed mutation modes:

- `worksheet/status mode`: worksheet, drift ledger, status, devlog, docs truth, and handoff truth only.
- `integration mode`: reviewed worker-patch integration only.
- `emergency repair mode`: recorded bypass only.

Every mutation mode must be announced before the first write:

`Current gate: <mode>; allowed write scope: <paths>; reason: <checkpoint/package>.`

Any unannounced direct `O-0` code edit is red drift and invalidates the package checkpoint until reviewed.

---

## preserved baseline

- Previous ontology artifact tranche is closed at `99e2ae8`.
- Existing CLI `mempalace ontology chatgpt-signals --no-dry-run` initializes a run shell only.
- Pure phase modules exist for `pass1_open`, `candidate_clusters`, `canonical_candidates`, `route_candidates`, `route_pass2`, `route_verify`, iteration decisions, convergence reports, and apply-ready manifests.
- MCP read path `mempalace_export_drawers` exports full drawer content read-only with safe metadata.
- MCP apply path `mempalace_copy_drawer` creates deterministic semantic copies and leaves source drawers untouched.
- Dashboard ontology endpoints and UI already read `progress.json`, `artifacts_index.json`, and bounded unresolved previews.
- LocalAI helper script already refuses `api.openai.com` base URLs and uses LocalAI token files under `/media/u0/OneDrive_Backup/mempalace/secrets`.
- `chatgpt_signals` is source evidence, not the final semantic taxonomy.

---

## agent pool

| ID | Model | Depth | Role | Intended use | Forbidden use |
|---|---|---:|---|---|---|
| O-0 | `gpt-5.5` | xhigh | Orchestrator/integrator | Assign, review, checkpoint, integrate | package implementation |
| A-1 | `gpt-5.4` | high | Runner lead | resumable runner design and phase orchestration | MCP mutation implementation |
| A-2 | `gpt-5.4` | high | Safety lead | LocalAI/cloud refusal, source/apply idempotency, lock review | implementing under review |
| B-1 | `gpt-5.3-codex` | medium | Runner worker | `mempalace/ontology_runner.py`, CLI wiring, runner tests | docs-only closure |
| B-2 | `gpt-5.4-mini` | medium | Ops/docs worker | systemd wrapper/deploy docs, manual updates | runner algorithm ownership |
| B-3 | `gpt-5.4-mini` | medium | Test worker | fixtures, fake MCP/LocalAI providers, regression tests | broad refactors |
| R-1 | `gpt-5.4` | high | Independent reviewer | final no-delete/no-cloud/no-source-mutate review | implementation patching |

---

## package overview

| Package | Lead | Purpose | Size | Blocked by? |
|---|---|---:|---:|---|
| WP-00 | O-0 | Save continuation worksheet and freeze baseline | S | none |
| WP-01 | B-1 | Add resumable runner core and CLI phase execution | M | WP-00 |
| WP-02 | B-3 | Add contract and resume tests with fake MCP/LocalAI providers | S | WP-01 |
| WP-03 | B-2 | Add service wrapper/docs/manual for running on `snow-white-iii` | S | WP-01 |
| WP-04 | A-2/R-1 | Independent safety review and remediation loop | S | WP-01-WP-03 |
| WP-05 | O-0 | Integration verification, docs/devlog, commit, push | S | WP-04 |

---

## orchestration protocol

Workers own bounded packages. `O-0` assigns, reviews, accepts or rejects, records drift, and integrates only after evidence.

### Implementation ownership rule

Workers implement bounded packages. `O-0` assigns, reviews, accepts/rejects, records drift, and integrates only after evidence. `O-0` must not preempt worker implementation because a change appears obvious.

### Submilestone loop

1. `O-0` rereads this worksheet.
2. `O-0` activates one package or a non-conflicting parallel package set.
3. Worker implements within assigned write scope only.
4. Worker returns changed paths, behavior summary, tests/checks, and known gaps.
5. `O-0` reviews evidence against checkpoint requirements.
6. Independent review runs before any apply-capable path is accepted.
7. `O-0` records green/amber/red checkpoint verdict.
8. Only green checkpoints unlock downstream work.

### Progress/materialization rule

The runner must write durable artifacts progressively:

- update `progress.json` after every durable batch or record
- append phase records to the matching JSONL file
- refresh `artifacts_index.json` after writes
- append `accepted_routes.jsonl` and `unresolved.jsonl` as soon as route verification decisions are folded
- write `convergence_report.json` and `apply_ready_manifest.json` atomically

Progress cannot exist only in terminal output.

### Evidence rules

Acceptable evidence:

- fake-MCP tests proving paginated export and no source mutation
- fake-LocalAI tests proving prompt calls, invalid output durability, and cloud-base refusal
- resume tests proving already-written phase records are not duplicated
- progress tests proving dashboard-readable counts update during partial runs
- apply dry-run tests proving copies are not materialized unless explicitly requested
- apply tests against fake or tiny palace only
- final review proving no delete path and no cloud fallback

Insufficient evidence:

- CLI help output only
- worker summary without tests
- final report without intermediate artifacts
- LocalAI prompt code that does not write phase JSONL incrementally
- applying copies without local verifier approval
- any in-place update to source `chatgpt_signals`

---

## checkpoints and gates

### Checkpoint A - Worksheet Continuation Green

- **Proves:** runnable-runner work has a saved mutation-lock worksheet.
- **Required evidence:** worksheet exists on disk; branch/head/status recorded; O-0 model/depth recorded; out-of-scope dirty files noted.
- **Insufficient evidence:** worksheet only in chat.
- **Disposition:** green unlocks WP-01 through WP-03.

### Checkpoint B - Runner Core Green

- **Proves:** one command can execute ontology phases with LocalAI and progressive artifacts.
- **Required evidence:** CLI wiring, fake-provider tests, phase JSONL writes, progress/index updates, resume behavior, LocalAI cloud refusal.
- **Insufficient evidence:** run shell initialization only.
- **Disposition:** green unlocks ops/docs and review.

### Checkpoint C - Apply Safety Green

- **Proves:** semantic copies remain explicit, idempotent, and source-preserving.
- **Required evidence:** apply defaults to off/dry-run; apply path uses `apply_ready_manifest`; tests prove no copy without explicit apply and no source mutation.
- **Insufficient evidence:** manifest exists without copy-path test.
- **Disposition:** green unlocks final safety review.

### Checkpoint D - snow-white-iii Operation Green

- **Proves:** operator can run the runner on `snow-white-iii` under resource constraints without cloud LLMs.
- **Required evidence:** documented command/service wrapper uses LocalAI on `snow-white-iii`, 200% CPU cap, 16G memory cap, canonical OneDrive path, and no Extreme SSD.
- **Insufficient evidence:** local-only command with no deployment context.
- **Disposition:** green unlocks release verification.

### Checkpoint E - Release Green

- **Proves:** implementation is safe to push and hand off.
- **Required evidence:** targeted tests pass or blockers documented; docs/devlog updated; out-of-scope files unstaged; commit pushed to fork target.
- **Insufficient evidence:** unreviewed patch or incomplete worksheet ledger.
- **Disposition:** tranche closed.

---

## detailed work packages

### WP-00 - Worksheet and Baseline Freeze

- **owner:** `O-0`
- **lead:** `O-0`
- **support:** none
- **objective:** save this continuation worksheet and freeze repo/worktree truth.
- **why:** the previous tranche delivered phase modules but not an executable runner.
- **files/subsystems:** `docs/worksheets/mempalace_chatgpt_signal_ontology_runner_worksheet_2026-05-05.md`
- **deliverables:** saved worksheet with truthful branch/head/status and explicit `O-0` `gpt-5.5/xhigh`.
- **acceptance:** Checkpoint A green.
- **exit:** WP-01 through WP-03 activation.

### WP-01 - Resumable Runner Core and CLI

- **owner:** `O-0`
- **lead:** `B-1`
- **support:** `A-1`, `B-3`
- **objective:** add a LocalAI-backed runner that exports drawers, executes ontology phases, writes progressive artifacts, and resumes safely.
- **why:** the operator needs a real re-mining command, not just a run-shell initializer.
- **files/subsystems:** `mempalace/ontology_runner.py`, `mempalace/cli.py`, focused runner tests.
- **deliverables:** CLI flags for phase execution, LocalAI/MCP configuration, limit/resume controls, optional apply flag, progressive artifact writer.
- **acceptance:** Checkpoint B and Checkpoint C green.
- **exit:** WP-04 review.

### WP-02 - Runner Tests and Fixtures

- **owner:** `O-0`
- **lead:** `B-3`
- **support:** `B-1`
- **objective:** cover runner behavior with fake MCP and fake LocalAI providers.
- **why:** the runner must be testable without touching the hosted palace or LocalAI.
- **files/subsystems:** `tests/test_ontology_runner.py`, existing ontology tests if needed.
- **deliverables:** tests for paginated export, phase writes, invalid output, resume, no-apply default, apply dry-run, and progress updates.
- **acceptance:** test suite proves behavior without remote side effects.
- **exit:** WP-04 review.

### WP-03 - snow-white-iii Ops and Manuals

- **owner:** `O-0`
- **lead:** `B-2`
- **support:** none
- **objective:** document and wrap safe operation on `snow-white-iii`.
- **why:** the canonical palace runs on `snow-white-iii` for tailnet clients.
- **files/subsystems:** `scripts/systemd/`, `docs/manuals/`, `docs/chatgpt_signal_ontology_artifacts.md`, `CHANGELOG.md` as needed.
- **deliverables:** command/service guidance for LocalAI-only runner, CPU/memory caps, canonical paths, dashboard progress URL guidance, and no-Extreme-SSD guard.
- **acceptance:** Checkpoint D green.
- **exit:** WP-04 review.

### WP-04 - Independent Safety Review

- **owner:** `O-0`
- **lead:** `A-2` or `R-1`
- **support:** none
- **objective:** review the accepted diff for no-delete/no-cloud/no-source-mutate/apply-idempotency risks.
- **why:** this runner touches private content and may materialize copies.
- **files/subsystems:** accepted runner, tests, docs, worksheet.
- **deliverables:** review verdict with findings or explicit no-issue statement.
- **acceptance:** all high/medium findings resolved or explicitly deferred.
- **exit:** WP-05.

### WP-05 - Integration, Docs, Commit, Push

- **owner:** `O-0`
- **lead:** `O-0`
- **support:** none
- **objective:** integrate accepted worker patches, update worksheet/devlog/docs, verify, commit, and push.
- **why:** branch truth must match runnable behavior.
- **files/subsystems:** accepted worker changes, worksheet, docs/changelog.
- **deliverables:** final verification log, milestone commit, fork push.
- **acceptance:** Checkpoint E green.
- **exit:** tranche closed and runner can be deployed/run.

---

## assumptions

- The first real run reads existing `chatgpt_signals` drawers from the hosted palace.
- LocalAI completion endpoint is `http://snow-white-iii:8080/v1/chat/completions` via base URL `http://snow-white-iii:8080/v1`.
- LocalAI token file is `/media/u0/OneDrive_Backup/mempalace/secrets/localai_token`.
- MemPalace HTTP MCP token file is `/media/u0/OneDrive_Backup/mempalace/secrets/http_token`.
- Default model remains `qwen3-vl-8b-instruct` unless runtime env overrides it.
- Runner default is no semantic apply; `--apply-copies` must be explicit.
- Dashboard watches artifacts under `/media/u0/OneDrive_Backup/mempalace/data/ontology`.
- A first implementation can run candidate naming, route pass, and verification sequentially with bounded limits; later batching can optimize throughput.

---

## checkpoint ledger

| Checkpoint | Status | Evidence | Next gate |
|---|---|---|---|
| A - Worksheet Continuation Green | green | Worksheet saved on disk; branch/head/status recorded; O-0 model/depth recorded; out-of-scope dirty files noted. | WP-01/WP-02/WP-03 |
| B - Runner Core Green | pending | none yet | WP-04 |
| C - Apply Safety Green | pending | none yet | WP-04 |
| D - snow-white-iii Operation Green | green | WP-03 docs accepted: systemd README/env template/manual/changelog document snow-white-iii, LocalAI-only endpoint, canonical OneDrive paths, 200% CPU/16G memory caps, read-only dashboard progress, and no apply without explicit flag. | WP-04 after runner core |
| E - Release Green | pending | none yet | tranche closed |

---

## package status ledger

| Package | Status | Owner | Notes |
|---|---|---|---|
| WP-00 | complete | O-0 | Worksheet saved and Checkpoint A is green. |
| WP-01 | active | B-1/Planck | Runner core and CLI assigned. |
| WP-02 | pending | B-3 | blocked by Checkpoint A |
| WP-03 | complete | B-2/Galileo | Ops/docs accepted; no deployment performed. |
| WP-04 | pending | A-2/R-1 | blocked by WP-01-WP-03 |
| WP-05 | pending | O-0 | blocked by WP-04 |

---

## drift ledger

### Open drift items

- Out-of-scope dirty `.agents/plugins/marketplace.json` exists. Do not stage or modify it.
- Unaccepted untracked `docs/reference/` exists from the prior tranche. Do not stage, rewrite, or delete it without explicit user confirmation.

### Drift recording rule

Any deviation from this worksheet must be recorded here before the next package closes, including changed paths, violated gate, reason, recovery action, and current verdict.

### Red drift conditions

- `O-0` directly edits implementation files outside a declared mutation mode.
- Any source `chatgpt_signals` drawer is mutated in place.
- Any delete or cleanup touches palace data without explicit confirmation.
- Any cloud LLM upload happens without separate explicit approval.
- Dashboard progress reads trigger Chroma writes, LocalAI calls, mining, classification, or ontology mutation.
- Progress exists only in terminal output and is not materialized to run artifacts.

---

## evidence log

### 2026-05-05 - WP-00 Baseline Evidence

- `git rev-parse --short HEAD` reported `99e2ae8`.
- `git status --short --branch` showed branch `codex/mempalace-http-mcp-closure` with out-of-scope dirty `.agents/plugins/marketplace.json` and unaccepted untracked `docs/reference/`.
- `git remote -v` showed local `origin` as upstream `git@github.com:MemPalace/mempalace.git`; fork push target remains explicit.
- `tako_orchestrated_worksheet_template_mutation_lock_2026-05-03.md` was found at `/home/u4/tako_orchestrated_worksheet_template_mutation_lock_2026-05-03.md` and used for this worksheet structure.

### 2026-05-05 - WP-00 Milestone Commit Evidence

- `git add docs/worksheets/mempalace_chatgpt_signal_ontology_runner_worksheet_2026-05-05.md` staged only the continuation worksheet.
- `git diff --cached --check` passed.
- `git commit -m "Add ChatGPT ontology runner worksheet"` created `d68feee`.
- `git push git@github.com:botman058/mempalace.git HEAD:refs/heads/codex/mempalace-http-mcp-closure` pushed `d68feee` to the fork branch.

### 2026-05-05 - WP-01 and WP-03 Activation

- `O-0` reread this worksheet before activation.
- WP-01 was assigned to B-1/Planck with model `gpt-5.3-codex` and reasoning depth `medium`.
- B-1 write scope is limited to `mempalace/ontology_runner.py`, `mempalace/cli.py`, and focused runner/CLI tests.
- WP-03 was assigned to B-2/Galileo with model `gpt-5.4-mini` and reasoning depth `medium`.
- B-2 write scope is limited to `scripts/systemd/README.md`, `scripts/systemd/mempalace.env.template`, optional ontology runner systemd wrapper/unit files, `docs/manuals/mempalace_dashboard_end_user_manual_2026-05-04.md`, and `CHANGELOG.md`.
- Both workers were instructed not to touch `.agents/plugins/marketplace.json`, unaccepted `docs/reference/`, source palace data, or each other's files.

### 2026-05-05 - WP-03 Acceptance Evidence

- B-2/Galileo changed only `scripts/systemd/README.md`, `scripts/systemd/mempalace.env.template`, `docs/manuals/mempalace_dashboard_end_user_manual_2026-05-04.md`, and `CHANGELOG.md`.
- The docs now state that the ontology runner is intended for `snow-white-iii` under the `mempalace` service user and canonical `/media/u0/OneDrive_Backup/mempalace` paths.
- The docs explicitly refuse `/media/u0/Extreme SSD` for this workflow.
- LocalAI is documented as `http://snow-white-iii:8080/v1` with token file `/media/u0/OneDrive_Backup/mempalace/secrets/localai_token`, not a cloud endpoint.
- Resource guidance records `CPUQuota=200%` and `MemoryMax=16G` for any wrapper.
- The dashboard manual and systemd README describe ontology progress as read-only artifacts under `/media/u0/OneDrive_Backup/mempalace/data/ontology/<run_id>/`.
- The docs preserve the safe default: producing `apply_ready_manifest.json` does not copy drawers unless an explicit apply flag is used.
- `git diff --check -- CHANGELOG.md scripts/systemd/README.md scripts/systemd/mempalace.env.template docs/manuals/mempalace_dashboard_end_user_manual_2026-05-04.md docs/worksheets/mempalace_chatgpt_signal_ontology_runner_worksheet_2026-05-05.md` passed.
- Known gap: no new systemd wrapper/unit was added and no deployment or runtime verification was performed.
