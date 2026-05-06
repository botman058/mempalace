# MemPalace ChatGPT Thread Signal Rebuild - Orchestrated Worksheet
Date: 2026-05-06
Repo baseline: `/home/u4/repos/mempalace`
Live branch baseline: `codex/mempalace-http-mcp-closure` at `63e2c3e`
Observed branch relation: local checkout on closure branch; out-of-scope dirty `.agents/plugins/marketplace.json` and unaccepted untracked `docs/reference/` remain present
Document type: implementation worksheet
Objective: replace the front-biased `chatgpt_signals` extraction with a high-recall, thread-aware LocalAI signal layer that covers long ChatGPT conversations, preserves multiple subthreads per conversation, writes auditable `chatgpt_thread_signals` source drawers, and then runs ontology recovery over that new source wing without deleting or mutating raw evidence.

---

## control plane

### Top-level orchestrator

- **Only top-level orchestrator:** `O-0`
- **Model:** `gpt-5.5`
- **Reasoning depth:** `xhigh`
- **Authority:** assign packages, enforce mutation lock, review evidence, arbitrate architecture, integrate accepted patches, update worksheet/devlog/docs truth, commit, push milestones, and perform explicitly scoped live service operations on `snow-white-iii`
- **Forbidden uses:** direct package implementation, deleting files or palace data, mutating existing `chatgpt` or `chatgpt_signals` drawers, touching `.agents/plugins/marketplace.json`, staging unaccepted `docs/reference/`, using `/media/u0/Extreme SSD`, cloud LLM upload without separate explicit approval, and applying semantic copies before manual inspection
- **Mutation lock:** `O-0` is read/review/orchestrate-only by default. Direct implementation edits are forbidden except in declared worksheet/status, integration, or emergency repair mode.

### O-0 mutation lock

`O-0` is read/review/orchestrate-only until a package has explicit activation, bounded worker ownership, returned implementation evidence, required independent review, and an `O-0` checkpoint verdict.

`O-0` must not directly edit repo files, call `apply_patch`, run write commands, run rewriting formatters, generate migrations/codegen, stage commits, or push during package implementation.

Allowed mutation modes:

- `worksheet/status mode`: worksheet, drift ledger, status, devlog, docs truth, handoff truth, and live-run evidence only.
- `integration mode`: reviewed worker-patch integration only.
- `emergency repair mode`: recorded bypass only.

Every mutation mode must be announced before the first write:

`Current gate: <mode>; allowed write scope: <paths>; reason: <checkpoint/package>.`

Any unannounced direct `O-0` code edit is red drift and invalidates the package checkpoint until reviewed.

### Working rule

One worksheet controls this tranche:
`docs/worksheets/mempalace_chatgpt_thread_signal_rebuild_worksheet_2026-05-06.md`.

`O-0` rereads this worksheet before package activation, worker acceptance, checkpoint closure, live service operations, docs/devlog updates, staging, commit, and push.

### Current hard gate

Checkpoint C, Checkpoint D, Checkpoint E, and Checkpoint F are green after O-0 review. WP-07 and WP-08 may be activated in bounded worker-owned slices. WP-09 remains blocked until runner/docs and consolidated verification are accepted.

---

## reasoning-depth matrix

| Model | Reasoning depth | Intended uses | Forbidden uses |
|---|---:|---|---|
| `gpt-5.5` | xhigh | `O-0` orchestration, checkpoint verdicts, architecture arbitration, integration | direct package implementation outside declared mutation modes |
| `gpt-5.4` | high | segmentation/subthread architecture, LocalAI extraction/reconciliation design, independent safety review | bounded implementation patches after review role is assigned |
| `gpt-5.3-codex` | medium | bounded production code patches with explicit file ownership | architecture arbitration or independent final safety review |
| `gpt-5.4-mini` | medium | focused tests, docs, systemd wrappers, fixture generation | safety arbitration or large algorithm ownership |
| `gpt-5.3-codex-spark` | medium | narrow syntax/test verification and fixture checks | broad refactors or mutation-path design |

---

## standing constraints

1. Do not delete files or palace data without explicit confirmation.
2. Do not mutate existing `chatgpt` raw drawers.
3. Do not mutate existing `chatgpt_signals` drawers; they remain flawed preview/audit evidence.
4. New recovered source drawers must default to wing `chatgpt_thread_signals`.
5. Final semantic organization remains canonical `wing:room` ontology routing after recovered signals exist.
6. Do not overwrite outside explicitly designated working folders.
7. Canonical remote root remains `/media/u0/OneDrive_Backup/mempalace`.
8. Do not use `/media/u0/Extreme SSD`.
9. LocalAI is hosted on `snow-white-iii`; cloud LLM APIs are forbidden unless the user separately approves a previewed batch.
10. CPU cap target remains 200%; memory cap target remains 16G for long-running services.
11. The dashboard and HTTP MCP services must not trigger hidden writes beyond explicitly invoked write tools.
12. Any semantic copy/apply path remains off until manual inspection of manifests.
13. Use deterministic IDs, source hashes, and resumable checkpoints so reruns are idempotent.
14. Do not stage or modify `.agents/plugins/marketplace.json`.
15. Do not stage, rewrite, or delete unaccepted `docs/reference/`.
16. Push accepted milestones explicitly to `git@github.com:botman058/mempalace.git HEAD:refs/heads/codex/mempalace-http-mcp-closure`.

---

## preserved baseline

- Raw `chatgpt` wing exists on `snow-white-iii` with `135,182` drawers.
- Existing `chatgpt_signals` wing exists with `9,598` drawers.
- Staged ChatGPT source tree contains `19` `conversations.json` exports under `/media/u0/OneDrive_Backup/mempalace/sources/chatgpt`.
- Existing LocalAI signal checkpoint has `1,781` rows: `1,733` classified and `48` skipped empty.
- Existing `scripts/localai_chatgpt_signals.py` is front-biased because it truncates with `transcript[:12000]`.
- Measured staged archive contains `4,283` conversations; `1,857` transcripts exceed 12k chars; `1,168` exceed 24k; `219` exceed 100k; `240` first messages exceed 12k.
- The active run `20260505T175609Z_chatgpt_signal_ontology` reads `chatgpt_signals`; it is superseded by this tranche and is not trusted as final.
- Existing ontology runner can read an arbitrary source wing via `--source-wing`.
- Existing MCP read path `mempalace_export_drawers` is read-only and paginated.
- Existing MCP copy path `mempalace_copy_drawer` creates deterministic semantic copies and leaves source drawers untouched.
- Existing app deployment on `snow-white-iii` is a staged copy, not a git checkout.

---

## agent pool

| ID | Model | Depth | Role | Intended use | Forbidden use |
|---|---|---:|---|---|---|
| O-0 | `gpt-5.5` | xhigh | Orchestrator/integrator | Assign, review, checkpoint, integrate, update worksheet/status | direct package implementation |
| A-1 | `gpt-5.4` | high | Thread architecture lead | segmentation, subthread identity, coverage invariants | MCP mutation implementation |
| A-2 | `gpt-5.4` | high | Extraction/reconciliation lead | LocalAI prompts, segment signal folding, checkpoint semantics | final safety review |
| A-3 | `gpt-5.4` | high | Safety reviewer | no-delete/no-cloud/no-source-mutate/idempotency review | implementation under review |
| B-1 | `gpt-5.3-codex` | medium | Segment worker | pure segmentation/subthread helper and tests | MCP/server mutation |
| B-2 | `gpt-5.3-codex` | medium | MCP/write worker | provenance-rich signal drawer write path and tests | LocalAI extraction algorithm |
| B-3 | `gpt-5.3-codex` | medium | Extractor worker | thread-aware LocalAI script/runner and checkpoint tests | independent review |
| B-4 | `gpt-5.4-mini` | medium | Ops/docs worker | systemd wrapper, operator docs, worksheet evidence | core extraction algorithm |
| B-5 | `gpt-5.4-mini` | medium | Verification worker | fixtures, smoke scripts, targeted test orchestration | broad refactors |

---

## package overview

| Package | Lead | Purpose | Size | Blocked by? |
|---|---|---:|---:|---|
| WP-00 | O-0 | Save worksheet and freeze baseline | S | none |
| WP-01 | O-0 | Stop and mark superseded current ontology run | S | WP-00 |
| WP-02 | A-1/B-1 | Add deterministic turn/window segmentation with oversize-message splitting | M | WP-00 |
| WP-03 | A-1/B-1 | Add stable intra-conversation subthread detection | M | WP-02 |
| WP-04 | A-2/B-3 | Add segment-level LocalAI extraction and checkpoint model | M | WP-03 |
| WP-05 | A-2/B-3 | Add conversation-level reconciliation/dedupe of segment signals | M | WP-04 |
| WP-06 | B-2 | Add provenance-rich `chatgpt_thread_signals` write path | M | WP-02 |
| WP-07 | B-4 | Add bounded snow-white runner/deploy docs for thread signal rebuild | S | WP-04, WP-06 |
| WP-08 | B-5 | Add targeted unit/integration tests and fixtures | M | WP-02-WP-06 |
| WP-09 | O-0 | Remote smoke with small limit and worksheet evidence | S | WP-07, WP-08 |
| WP-10 | O-0 | Full remote thread-signal rebuild | L | WP-09 |
| WP-11 | O-0 | Run ontology over `chatgpt_thread_signals` with apply off | M | WP-10 |
| WP-12 | A-3/O-0 | Independent safety review, docs/devlog, commit/push closure | S | WP-11 |

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
6. Independent review runs before any apply-capable path or full remote run is accepted.
7. `O-0` records green/amber/red checkpoint verdict.
8. Only green checkpoints unlock downstream work.

### Progress/materialization rule

The thread-signal rebuild must write durable artifacts progressively:

- `progress.json` after every processed segment or reconciled conversation
- append-only checkpoint JSONL keyed by conversation/source hash/segment/subthread
- bounded LocalAI raw-response excerpts for invalid outputs only
- final per-conversation reconciliation records
- summary report with coverage counts and truncation/oversize statistics

Progress cannot exist only in terminal output.

### Evidence rules

Acceptable evidence:

- tests proving no transcript suffix is dropped
- tests proving a first message over 12k chars is split and later turns remain reachable
- tests proving multiple subthreads inside one conversation can produce distinct stable IDs
- fake-LocalAI tests proving segment extraction, invalid-output durability, and cloud-base refusal
- MCP tests proving deterministic signal drawer writes and no mutation of `chatgpt` or `chatgpt_signals`
- checkpoint/resume tests proving reruns do not duplicate segment or final signal records
- snow-white smoke with `--limit` before full rebuild
- worksheet/live evidence after service operations

Insufficient evidence:

- worker summary without tests
- CLI help only
- a new script that still uses leading-char truncation
- a single conversation summary with no segment coverage proof
- docs claiming thread awareness without fixtures
- writing into `chatgpt_signals`
- applying ontology copies
- direct `O-0` implementation outside declared mutation mode

---

## checkpoints and gates

### Checkpoint A - Worksheet Green

- **Proves:** the thread-signal rebuild has a saved O-0 mutation-lock worksheet.
- **Required evidence:** worksheet exists on disk; branch/head/status recorded; current run and truncation measurements recorded; O-0 model/depth recorded.
- **Insufficient evidence:** plan only in chat.
- **Disposition:** green unlocks WP-01 through WP-03.

### Checkpoint B - Superseded Run Safe

- **Proves:** the flawed ontology run is stopped without deleting artifacts.
- **Required evidence:** systemd unit inactive/dead or stopped; run id recorded; no files deleted; worksheet status updated.
- **Insufficient evidence:** assuming the run will end naturally.
- **Disposition:** green unlocks remote rebuild work.

### Checkpoint C - Coverage Segmenter Green

- **Proves:** conversation coverage is complete before LocalAI calls.
- **Required evidence:** tests for short, long, huge first-message, and multi-turn conversations; deterministic segment IDs; no dropped suffix.
- **Insufficient evidence:** manual inspection of one transcript.
- **Disposition:** green unlocks extraction/reconciliation.

### Checkpoint D - Subthread Green

- **Proves:** one conversation may produce multiple stable internal subthreads.
- **Required evidence:** tests with mixed-topic conversation fixture; stable subthread IDs; fallback behavior for ambiguous threads.
- **Insufficient evidence:** one room per conversation.
- **Disposition:** green unlocks reconciliation acceptance.

### Checkpoint E - Signal Write Safety Green

- **Proves:** recovered signals can be written idempotently without mutating old evidence.
- **Required evidence:** deterministic signal IDs; provenance metadata; no-op duplicate writes; tests proving old wings unchanged.
- **Insufficient evidence:** using generic `mempalace_add_drawer` without provenance/idempotency proof.
- **Disposition:** green unlocks remote smoke.

### Checkpoint F - Extract/Reconcile Green

- **Proves:** LocalAI extraction and conversation-level folding are resumable and high recall.
- **Required evidence:** fake provider tests; checkpoint tests; invalid-output records; per-conversation dedupe/merge tests.
- **Insufficient evidence:** segment extraction without final reconciliation.
- **Disposition:** green unlocks ops wrapper and smoke.

### Checkpoint G - snow-white Smoke Green

- **Proves:** bounded live run works on `snow-white-iii` with LocalAI and resource caps.
- **Required evidence:** `--limit` smoke writes `chatgpt_thread_signals`; CPU/memory caps shown; LocalAI URL is local; no writes to old wings.
- **Insufficient evidence:** local tests only.
- **Disposition:** green unlocks full rebuild.

### Checkpoint H - Full Rebuild Green

- **Proves:** the complete staged archive has a recovered thread-aware signal layer.
- **Required evidence:** completion report; signal count; skipped/error counts; long-conversation coverage summary; checkpoint artifacts.
- **Insufficient evidence:** raw drawer count or old `chatgpt_signals` count.
- **Disposition:** green unlocks ontology over new wing.

### Checkpoint I - Ontology Re-run Green

- **Proves:** ontology can run over `chatgpt_thread_signals` with apply off.
- **Required evidence:** new ontology run id; progress artifacts; no copies materialized; dashboard-readable progress.
- **Insufficient evidence:** old `chatgpt_signals` ontology run.
- **Disposition:** green unlocks final review.

### Checkpoint J - Release Green

- **Proves:** branch is safe to hand off.
- **Required evidence:** targeted tests pass or blockers documented; independent safety review; docs/devlog updated; out-of-scope files unstaged; milestones pushed.
- **Insufficient evidence:** unreviewed patch or incomplete worksheet ledger.
- **Disposition:** tranche closed.

---

## detailed work packages

### WP-00 - Worksheet and Baseline Freeze

- **owner:** `O-0`
- **lead:** `O-0`
- **support:** none
- **objective:** create the live worksheet and freeze branch, data, and run truth.
- **why:** prevents drift into direct implementation or untracked operational state.
- **files/subsystems:** `docs/worksheets/mempalace_chatgpt_thread_signal_rebuild_worksheet_2026-05-06.md`
- **deliverables:** worksheet with control plane, roster, packages, gates, assumptions, and evidence log.
- **acceptance:** Checkpoint A green; worksheet committed and pushed.
- **exit:** WP-01 through WP-03 may be activated.

### WP-01 - Stop Superseded Ontology Run

- **owner:** `O-0`
- **lead:** `O-0`
- **support:** none
- **objective:** stop `mempalace-ontology-chatgpt-signals.service` without deleting run artifacts.
- **why:** user selected stop-and-redo because current source layer is front-biased and lossy.
- **files/subsystems:** `snow-white-iii` transient systemd unit and worksheet evidence only.
- **deliverables:** stopped unit, recorded run id/status, no cleanup.
- **acceptance:** Checkpoint B green.
- **exit:** remote resources available for rebuild smoke.

### WP-02 - Deterministic Segmenter

- **owner:** worker-owned
- **lead:** `A-1`
- **support:** `B-1`, `B-5`
- **objective:** add pure helpers that segment ChatGPT conversations without leading-char truncation.
- **why:** existing `transcript[:12000]` drops long-thread suffixes and oversized first-message content.
- **files/subsystems:** new or focused helpers under `mempalace/`; segmentation tests under `tests/`.
- **deliverables:** complete ordered segments, deterministic IDs, turn/message range metadata.
- **acceptance:** Checkpoint C green.
- **exit:** WP-03 and WP-04 may use segment contracts.

### WP-03 - Intra-conversation Subthread Detection

- **owner:** worker-owned
- **lead:** `A-1`
- **support:** `B-1`, `B-5`
- **objective:** detect stable subthreads inside a conversation and attach segment/subthread provenance.
- **why:** a single ChatGPT conversation may contain multiple unrelated or loosely related threads.
- **files/subsystems:** same pure helper family as WP-02 plus fixtures/tests.
- **deliverables:** stable `subthread_id`, label, confidence or fallback reason.
- **acceptance:** Checkpoint D green.
- **exit:** WP-05 can reconcile by conversation and subthread.

### WP-04 - Segment-level LocalAI Extraction

- **owner:** worker-owned
- **lead:** `A-2`
- **support:** `B-3`, `B-5`
- **objective:** run LocalAI over each segment/subthread record with fail-closed JSON parsing and progressive checkpoints.
- **why:** high recall requires all long-thread segments to be eligible for extraction.
- **files/subsystems:** new thread-signal script or module, fake LocalAI tests.
- **deliverables:** segment extraction records, invalid output records, local-only URL guard.
- **acceptance:** Checkpoint F extraction evidence green.
- **exit:** WP-05 reconciliation can fold segment signals.

### WP-05 - Conversation-level Reconciliation

- **owner:** worker-owned
- **lead:** `A-2`
- **support:** `B-3`, `B-5`
- **objective:** dedupe and merge extracted segment signals into final per-conversation/subthread signals.
- **why:** overlapping segments and repeated topics must not create noisy duplicates.
- **files/subsystems:** thread-signal script/module and reconciliation tests.
- **deliverables:** final signal records with provenance and deterministic `source_signal_id`.
- **acceptance:** Checkpoint F reconciliation evidence green.
- **exit:** WP-06 can write final signals idempotently.

### WP-06 - Provenance-rich Signal Drawer Write Path

- **owner:** worker-owned
- **lead:** `B-2`
- **support:** `A-2`, `B-5`
- **objective:** add a deterministic write path for final recovered signals into `chatgpt_thread_signals`.
- **why:** generic drawer writes lack enough idempotent provenance for a rebuild pass.
- **files/subsystems:** MCP write tool or narrow extension, tests.
- **deliverables:** deterministic signal drawer ID, flat provenance metadata, duplicate no-op behavior.
- **acceptance:** Checkpoint E green.
- **exit:** WP-07 and WP-09 can use the write path.

### WP-07 - snow-white Runner and Docs

- **owner:** worker-owned
- **lead:** `B-4`
- **support:** `O-0`
- **objective:** add bounded operational wrapper/docs for the thread-signal rebuild on `snow-white-iii`.
- **why:** full rebuild is long-running and must respect CPU/memory/path/cloud constraints.
- **files/subsystems:** `scripts/systemd/`, docs/manuals, changelog.
- **deliverables:** start script or documented systemd-run command, defaults, token paths, progress paths.
- **acceptance:** Checkpoint G preconditions green.
- **exit:** WP-09 remote smoke can run.

### WP-08 - Test and Fixture Consolidation

- **owner:** worker-owned
- **lead:** `B-5`
- **support:** `B-1`, `B-2`, `B-3`
- **objective:** ensure package tests prove end-to-end contracts without relying on live data.
- **why:** live snow-white runs are expensive and must not be the first proof of behavior.
- **files/subsystems:** targeted tests and fixtures.
- **deliverables:** targeted pytest/py_compile/ruff evidence.
- **acceptance:** all checkpoint C-F tests pass.
- **exit:** WP-09 smoke may start.

### WP-09 - Remote Smoke

- **owner:** `O-0`
- **lead:** `O-0`
- **support:** `B-4`
- **objective:** run a bounded `snow-white-iii` smoke against the staged archive.
- **why:** verifies LocalAI, MCP, resource caps, checkpoints, and write behavior before full rebuild.
- **files/subsystems:** live services and worksheet evidence only.
- **deliverables:** smoke run id, progress, sample signal drawers, no writes to old wings.
- **acceptance:** Checkpoint G green.
- **exit:** WP-10 full rebuild may start.

### WP-10 - Full Thread-signal Rebuild

- **owner:** `O-0`
- **lead:** `O-0`
- **support:** `B-4`
- **objective:** run the complete thread-aware signal rebuild on `snow-white-iii`.
- **why:** produce the recovered high-recall source layer.
- **files/subsystems:** live services and worksheet evidence only.
- **deliverables:** completed rebuild report and `chatgpt_thread_signals` corpus.
- **acceptance:** Checkpoint H green.
- **exit:** WP-11 ontology re-run may start.

### WP-11 - Ontology Over Recovered Signals

- **owner:** `O-0`
- **lead:** `O-0`
- **support:** `B-4`
- **objective:** run ontology over `chatgpt_thread_signals` with semantic copy apply disabled.
- **why:** produce inspectable canonical candidate routes from the recovered signal layer.
- **files/subsystems:** live ontology runner and worksheet evidence only.
- **deliverables:** ontology run id, dashboard-readable progress, apply-ready manifest only.
- **acceptance:** Checkpoint I green.
- **exit:** WP-12 final review.

### WP-12 - Safety Review and Release

- **owner:** `O-0`
- **lead:** `A-3`
- **support:** `B-5`
- **objective:** independently review no-delete/no-cloud/no-source-mutate/idempotency and close docs/devlog.
- **why:** this tranche touches extraction and write paths over private archive material.
- **files/subsystems:** read-only review, docs, changelog, worksheet.
- **deliverables:** review verdict, docs/devlog updates, milestone commit/push.
- **acceptance:** Checkpoint J green.
- **exit:** tranche closed.

---

## assumptions

- Control host is `snow-white-iii`.
- Canonical root is `/media/u0/OneDrive_Backup/mempalace`.
- New source wing default is `chatgpt_thread_signals`.
- Existing `chatgpt` and `chatgpt_signals` are read-only for this tranche.
- Subthread detection may be heuristic, but IDs must be deterministic for identical source text.
- Reconciliation should prefer recall over aggressive pruning.
- Long-running live operations may use `root@snow-white-iii` only for narrow service control/status when explicitly required; no cleanup/delete commands are allowed.
- Dashboard integration for thread-signal progress is optional unless a package explicitly adds it; durable progress artifacts are mandatory.
- Full rebuild starts only after a bounded remote smoke is green.

---

## drift ledger

No drift recorded yet.

---

## evidence log

### 2026-05-06 - WP-00 Baseline Evidence

- `git rev-parse --short HEAD` reported `63e2c3e`.
- `git status --short --branch` showed branch `codex/mempalace-http-mcp-closure` with out-of-scope dirty `.agents/plugins/marketplace.json` and unaccepted untracked `docs/reference/`.
- `git remote -v` showed local `origin` as upstream `git@github.com:MemPalace/mempalace.git`; fork push target remains explicit.
- `tako_orchestrated_worksheet_template_mutation_lock_2026-05-03.md` was read from `/home/u4/tako_orchestrated_worksheet_template_mutation_lock_2026-05-03.md` and used for this worksheet structure.
- `snow-white-iii` active superseded ontology run was observed as `20260505T175609Z_chatgpt_signal_ontology`, phase `pass1_open`, `6920` processed of currently discovered `7000`, `8` errors, and `copies_materialized: 0`.

### 2026-05-06 - WP-00 Milestone Commit Evidence

- `git add docs/worksheets/mempalace_chatgpt_thread_signal_rebuild_worksheet_2026-05-06.md` staged only the worksheet.
- `git diff --cached --check` passed.
- `git commit -m "Add ChatGPT thread signal rebuild worksheet"` created `44076d2`.
- `git push git@github.com:botman058/mempalace.git HEAD:refs/heads/codex/mempalace-http-mcp-closure` pushed `44076d2` to the fork branch.
- Checkpoint A verdict: green.

### 2026-05-06 - WP-01 Superseded Run Stop Evidence

- `O-0` reread the worksheet before live service action.
- `O-0` stopped `mempalace-ontology-chatgpt-signals.service` on `snow-white-iii` using direct `root@snow-white-iii` SSH.
- `systemctl show mempalace-ontology-chatgpt-signals.service` reported `ActiveState=inactive`, `SubState=dead`, `MainPID=0`, `Result=success`, and `ExecMainStatus=0`.
- No files or palace data were deleted.
- Latest superseded artifact remains `/media/u0/OneDrive_Backup/mempalace/data/ontology/20260505T175609Z_chatgpt_signal_ontology/progress.json`.
- That progress artifact still says `status: running`, phase `pass1_open`, and `6962` processed of discovered `7000` because `O-0` did not mutate old run artifacts in place.
- Checkpoint B verdict: green.

### 2026-05-06 - WP-02/WP-03/WP-06 Activation

- `O-0` reread this worksheet before package activation.
- WP-02 and WP-03 were assigned to B-1/Gibbs with model `gpt-5.3-codex` and reasoning depth `medium`.
- B-1 write scope is limited to a focused segmentation/subthread helper module under `mempalace/` and focused tests, preferably `tests/test_chatgpt_thread_segments.py`.
- WP-06 was assigned to B-2/Linnaeus with model `gpt-5.3-codex` and reasoning depth `medium`.
- B-2 write scope is limited to `mempalace/mcp_server.py`, `tests/test_mcp_server.py`, and only if needed one focused deterministic ID helper.
- Both workers were instructed that they are not alone in the codebase, must not revert others' edits, and must not touch `.agents/plugins/marketplace.json`, unaccepted `docs/reference/`, existing `chatgpt` or `chatgpt_signals` drawers, ontology runner files, extractor script files outside their scopes, or docs.

### 2026-05-06 - WP-02/WP-03 Acceptance Evidence

- `O-0` reread this worksheet before worker acceptance review.
- B-1/Gibbs returned new focused helper files `mempalace/chatgpt_thread_segments.py` and `tests/test_chatgpt_thread_segments.py`.
- `O-0` ran `.venv/bin/python -m pytest -q tests/test_chatgpt_thread_segments.py`: `6 passed in 0.35s`.
- `O-0` ran `.venv/bin/python -m py_compile mempalace/chatgpt_thread_segments.py tests/test_chatgpt_thread_segments.py`: passed.
- Coverage evidence includes short conversation, long multi-turn segmentation with overlap, first-message-over-12k splitting, no dropped oversized-message suffix, deterministic reruns, and multiple subthreads in one conversation.
- Checkpoint C verdict: green.
- Checkpoint D verdict: green.

### 2026-05-06 - WP-06 Rework Evidence

- `O-0` reread this worksheet before worker acceptance review.
- B-2/Linnaeus returned an MCP write-path patch in `mempalace/mcp_server.py` and `tests/test_mcp_server.py`.
- `O-0` ran `.venv/bin/python -m py_compile mempalace/mcp_server.py tests/test_mcp_server.py`: passed.
- `O-0` ran `.venv/bin/python -m pytest -q tests/test_mcp_server.py -k 'add_signal_drawer or tools_list'`: `4 failed, 2 passed, 84 deselected`.
- The two tools/list checks passed, but all four functional `mempalace_add_signal_drawer` checks returned `success: False`.
- Rework diagnosis: the patch sanitizes optional provenance fields with `sanitize_kg_value` even when they default to empty strings, so minimal valid signal writes fail before persistence.
- B-2 was sent remediation instructions within the original WP-06 write scope.
- Checkpoint E verdict: red until the reworked patch passes idempotent write and no-source-mutation tests.

### 2026-05-06 - WP-04 Activation

- `O-0` reread this worksheet before package activation.
- WP-04 was assigned to B-3/Curie with model `gpt-5.3-codex` and reasoning depth `medium`.
- B-3 write scope is limited to a new thread-aware extraction runner, focused tests, and only if needed one narrow extraction-specific pure helper.
- B-3 was instructed to use the accepted `mempalace/chatgpt_thread_segments.py` contract, avoid live network in tests, refuse cloud LLM URLs, write progressive `progress.json` and append-only segment artifacts, and avoid drawer writes/reconciliation/systemd/dashboard changes.

### 2026-05-06 - WP-06 Acceptance Evidence

- B-2/Linnaeus returned a scoped remediation in `mempalace/mcp_server.py`.
- Remediation allows empty/absent optional provenance fields while preserving required validation for `room`, `content`, and `source_signal_id`.
- `O-0` ran `.venv/bin/python -m py_compile mempalace/mcp_server.py tests/test_mcp_server.py`: passed.
- `O-0` ran `.venv/bin/python -m pytest -q tests/test_mcp_server.py -k 'add_signal_drawer or tools_list'`: `6 passed, 84 deselected in 15.66s`.
- Accepted behavior includes deterministic `drawer_thread_signal_<digest>` IDs, duplicate same-content no-op, fail-closed source-signal collision, provenance metadata, and tests proving existing `chatgpt` and `chatgpt_signals` drawers are not mutated.
- Checkpoint E verdict: green.

### 2026-05-06 - WP-04 Acceptance Evidence

- B-3/Curie returned new files `scripts/localai_chatgpt_thread_signals.py` and `tests/test_localai_chatgpt_thread_signals.py`.
- The runner uses the accepted `build_chatgpt_thread_segments(...)` contract instead of leading-character truncation.
- The runner writes progressive `progress.json`, append-only `segment_checkpoint.jsonl`, `segment_extractions.jsonl`, and `invalid_outputs.jsonl` under a run directory.
- Invalid LocalAI output is recorded durably and is not treated as a valid extraction.
- The runner includes a fake-provider seam for no-network tests and refuses cloud LLM provider URLs.
- `O-0` ran `.venv/bin/python -m py_compile scripts/localai_chatgpt_thread_signals.py`: passed.
- `O-0` ran `.venv/bin/python -m pytest -q tests/test_localai_chatgpt_thread_signals.py tests/test_chatgpt_thread_segments.py`: `11 passed in 0.54s`.
- Checkpoint F extraction verdict: green.

### 2026-05-06 - WP-05 Activation

- `O-0` reread this worksheet before package activation.
- WP-05 was assigned to B-3/Curie with model `gpt-5.3-codex` and reasoning depth `medium`, continuing from the accepted WP-04 runner.
- B-3 write scope remains limited to `scripts/localai_chatgpt_thread_signals.py` and `tests/test_localai_chatgpt_thread_signals.py`.
- B-3 was instructed to add offline conversation/subthread reconciliation from segment extraction artifacts into deterministic final signal records, preserve high recall, dedupe overlapping segment items, avoid drawer writes, and prove rerun idempotency.

### 2026-05-06 - WP-05 Acceptance Evidence

- B-3/Curie returned reconciliation changes in `scripts/localai_chatgpt_thread_signals.py` and `tests/test_localai_chatgpt_thread_signals.py`.
- The reconciliation pass reads `segment_extractions.jsonl`, groups by `logical_source_id`, `source_hash`, and `subthread_id`, and writes deterministic `reconciled_signals.jsonl`.
- Final signal records include deterministic `source_signal_id`, `room`, `content`, source/subthread provenance, `segment_ids`, `segment_refs`, bounded evidence, extraction version, and model.
- Tests prove overlapping items dedupe with merged segment provenance, distinct items remain separate, same-text items in separate subthreads stay distinct, reruns do not duplicate records, and records include fields needed by `mempalace_add_signal_drawer`.
- `O-0` ran `.venv/bin/python -m py_compile scripts/localai_chatgpt_thread_signals.py`: passed.
- `O-0` ran `.venv/bin/python -m pytest -q tests/test_localai_chatgpt_thread_signals.py tests/test_chatgpt_thread_segments.py`: `16 passed in 0.61s`.
- Checkpoint F reconciliation verdict: green.
- Checkpoint F overall verdict: green.
