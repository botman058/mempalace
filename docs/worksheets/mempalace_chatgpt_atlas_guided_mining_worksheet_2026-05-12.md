# MemPalace ChatGPT Atlas-Guided Mining - Orchestrated Worksheet
Date: 2026-05-12
Repo baseline: `/home/u4/repos/mempalace`
Live branch baseline: `codex/mempalace-http-mcp-closure` at `5fad9d9`
Observed branch relation: local checkout on closure branch; out-of-scope dirty `.agents/plugins/marketplace.json`; unaccepted untracked `docs/reference/` remains present
Document type: implementation worksheet
Objective: build an atlas-guided ChatGPT signal mining layer from the completed pre-LLM archive atlas by converting atlas topic clusters into candidate canonical `wing:room` scaffolds, constraining LocalAI segment extraction against those candidates, reconciling and deduping outputs, and publishing only after explicit review gates, without mutating raw `chatgpt`, old `chatgpt_signals`, partial `chatgpt_thread_signals`, or atlas artifacts.

---

## control plane

### Top-level orchestrator

- **Only top-level orchestrator:** `O-0`
- **Model:** `gpt-5.5`
- **Reasoning depth:** `xhigh`
- **Authority:** assign packages, enforce mutation lock, manage parallel worker lanes, review evidence, arbitrate architecture, integrate accepted patches, update worksheet/devlog/docs truth, commit, push milestones, and perform explicitly scoped live service operations on `snow-white-iii`
- **Forbidden uses:** direct package implementation, deleting files or palace data, mutating existing `chatgpt`, `chatgpt_signals`, `chatgpt_thread_signals`, or atlas artifacts, publishing without a review gate, touching `.agents/plugins/marketplace.json`, staging unaccepted `docs/reference/`, using `/media/u0/Extreme SSD`, cloud LLM calls, or resuming the stopped broad LocalAI grind as production work
- **Mutation lock:** `O-0` is read/review/orchestrate-only by default. Direct implementation edits are forbidden except in declared worksheet/status, integration, or emergency repair mode.

### Working rule

One new worksheet controls this tranche:

`docs/worksheets/mempalace_chatgpt_atlas_guided_mining_worksheet_2026-05-12.md`

`O-0` rereads this worksheet before package activation, worker acceptance, checkpoint closure, live service operations, docs/devlog updates, staging, commit, and push.

All subagents must be spawned with explicit model and reasoning depth. `O-0` must not let workers inherit model size or reasoning depth by default.

### Current hard gate

Checkpoint B is the active gate. `WP-01` artifact contract work is the only package unlocked after Checkpoint A. No atlas-guided bridge implementation, runner, LocalAI call, remote unit, publish attempt, or documentation outside the WP-01 write scope may start before WP-01 closes.

---

## reasoning-depth matrix

| Model | Reasoning depth | Intended uses | Forbidden uses |
|---|---:|---|---|
| `gpt-5.5` | `xhigh` | `O-0` orchestration, checkpoint verdicts, architecture arbitration | direct package implementation outside declared mutation modes |
| `gpt-5.5` | `high` | contract lead, independent safety review, high-stakes schema arbitration | bounded helper patch work |
| `gpt-5.4` | `high` | atlas bridge architecture, LocalAI prompt/extraction architecture, reconciliation/routing architecture, live ops strategy | independent final review of own implementation |
| `gpt-5.3-codex` | `medium` | bounded implementation workers with explicit file ownership | package leadership, architecture arbitration, final safety review |
| `gpt-5.3-codex-spark` | `high` | focused fixtures, parser tests, syntax/static verification, artifact-shape checks | package leadership or safety arbitration |
| `gpt-5.4-mini` | `medium` | docs/operator wording, small dashboard or report helpers | core mining architecture |

---

## standing constraints

1. Do not delete files or palace data without explicit confirmation.
2. Do not mutate existing `chatgpt` raw drawers.
3. Do not mutate existing `chatgpt_signals` drawers.
4. Do not mutate or resume the partial `chatgpt_thread_signals` run as production output.
5. Do not overwrite or rewrite completed atlas artifacts.
6. Do not publish any atlas-guided output before Checkpoint K is green.
7. First publish target, if approved, is a new wing: `chatgpt_atlas_signals`.
8. Default live extraction runs are no-publish.
9. LocalAI must be hosted on `snow-white-iii`; cloud LLM APIs are forbidden.
10. Canonical remote root remains `/media/u0/OneDrive_Backup/mempalace`.
11. New atlas-guided run artifacts must live under `/media/u0/OneDrive_Backup/mempalace/data/atlas_guided_chatgpt_signals/<run_id>/`.
12. Do not use `/media/u0/Extreme SSD`.
13. Long remote work runs on `snow-white-iii` as service user `mempalace`.
14. CPU cap target remains `200%`; memory cap target remains `16G`.
15. Dashboard and HTTP MCP services must not trigger hidden write paths during active mining.
16. Use deterministic IDs, source hashes, candidate IDs, and resumable checkpoints so reruns are idempotent.
17. Preserve prior partial-run artifacts as diagnostic evidence only.
18. Do not stage or modify `.agents/plugins/marketplace.json`.
19. Do not stage, rewrite, or delete unaccepted `docs/reference/`.
20. Push accepted milestones to `git@github.com:botman058/mempalace.git HEAD:refs/heads/codex/mempalace-http-mcp-closure`.

---

## O-0 mutation lock

`O-0` is read/review/orchestrate-only until a package has:

1. explicit activation,
2. a bounded worker owner,
3. returned implementation evidence,
4. independent review where required,
5. an `O-0` checkpoint verdict.

`O-0` must not directly edit repo files, call `apply_patch`, run write commands, run rewriting formatters, generate migrations/codegen, stage commits, or push during package implementation.

Allowed mutation modes:

- `worksheet/status mode`: worksheet, drift ledger, status, devlog, docs truth, handoff truth, and live-run evidence only.
- `integration mode`: reviewed worker-patch integration only.
- `emergency repair mode`: recorded bypass only.

Every mutation mode must be announced before the first write:

`Current gate: <mode>; allowed write scope: <paths>; reason: <checkpoint/package>.`

Any unannounced direct `O-0` code edit is red drift and invalidates the package checkpoint until reviewed.

---

## preserved baseline

- Raw `chatgpt` wing exists on `snow-white-iii` with about `135,182` drawers.
- Existing `chatgpt_signals` wing exists with about `9,598` drawers and is not trusted as final semantic organization.
- Existing `chatgpt_thread_signals` wing contains only smoke/partial evidence, about `3` drawers.
- Completed atlas run is canonical input: `/media/u0/OneDrive_Backup/mempalace/data/chatgpt_archive_atlas/atlas_full2_20260512T0412Z_2fc8ac5`.
- Atlas run counts: `4,283` conversations, `4,746` threads, `3,120` topic clusters, `4,746` CUDA embedding rows, `63` source errors, `2` warnings.
- Atlas artifacts include `topic_clusters.jsonl`, `thread_index.jsonl`, `lexical_sketches.jsonl`, `thread_embeddings.jsonl`, `thread_embedding_vectors.jsonl`, `atlas_summary.md`, `progress.json`, and `artifacts_index.json`.
- Atlas worksheet is closed green; atlas artifacts are pre-LLM, artifact-only, and not published as drawers.
- Prior broad thread-signal run directory remains diagnostic-only: `/media/u0/OneDrive_Backup/mempalace/data/localai_chatgpt_thread_signals/20260506031028_thread_signal_rebuild`.
- Prior broad thread-signal preview found useful extraction direction but poor seed-type distribution, inflated importance, weak subthread labels, and visible overlap duplicates.
- `scripts/localai_chatgpt_thread_signals.py` currently does not consume atlas artifacts.
- Existing ontology modules provide reusable pure helpers for candidate clusters, canonical candidates, route candidates, route pass, verification, and iteration reports.
- Existing thread segmentation machinery preserves long conversations better than the old front-biased `chatgpt_signals` pass.
- `mempalace-http.service` and `mempalace-dashboard.service` are expected to remain hosted on `snow-white-iii`.
- Current local branch is `codex/mempalace-http-mcp-closure` at `5fad9d9`.
- Current dirty files remain out of scope: modified `.agents/plugins/marketplace.json` and untracked `docs/reference/`.

---

## agent pool

| ID | Model | Depth | Role | Intended use | Forbidden use |
|---|---|---:|---|---|---|
| `O-0` | `gpt-5.5` | xhigh | Owner/orchestrator | assign, review, checkpoint, integrate, update worksheet/status | implementation lead or direct package coding |
| `L-1` | `gpt-5.5` | high | Contract and safety lead | artifact schemas, no-write contract, acceptance contract, high-risk invariants | parser or runner implementation |
| `L-2` | `gpt-5.4` | high | Atlas bridge lead | atlas artifact semantics, cluster-to-candidate mapping, coverage invariants | LocalAI prompt implementation |
| `L-3` | `gpt-5.4` | high | Extraction prompt lead | atlas-guided LocalAI prompt, parser, invalid-output policy | final safety review |
| `L-4` | `gpt-5.4` | high | Reconciliation and routing lead | dedupe, candidate-aware reconciliation, publish readiness | MCP write implementation |
| `L-5` | `gpt-5.4` | high | Live ops and resource-safety lead | snow-white runner strategy, service caps, no-publish live run design | taxonomy architecture ownership |
| `H-1` | `gpt-5.3-codex` | medium | Atlas adapter helper | bounded atlas artifact reader/mapper patches | architecture decisions |
| `H-2` | `gpt-5.3-codex` | medium | Extractor helper | bounded runner/prompt plumbing patches | prompt architecture ownership |
| `H-3` | `gpt-5.3-codex` | medium | Reconciliation helper | bounded reconciliation and publish-metadata patches | final safety review |
| `H-4` | `gpt-5.3-codex` | medium | Ops helper | bounded shell wrapper and deployment helper patches | live-run authority |
| `H-5` | `gpt-5.4-mini` | medium | Docs/report helper | operator docs, review summaries, dashboard wording | core algorithm implementation |
| `T-1` | `gpt-5.3-codex-spark` | high | Test helper | fixtures, parser tests, fake providers, static checks | package leadership |
| `V-1` | `gpt-5.3-codex-spark` | high | Verification helper | syntax, `bash -n`, targeted tests, remote artifact checks | implementation under review |
| `R-1` | `gpt-5.5` | high | Independent reviewer | no-delete/no-cloud/no-unreviewed-publish/idempotency review | implementation ownership |

---

## package overview

| Package | Lead | Support | Purpose | Size | Blocked by? | Parallel lane |
|---|---|---|---|---:|---|---|
| WP-00 | `O-0` status-only | none | Create worksheet and freeze baseline | S | none | gate |
| WP-01 | `L-1` | `T-1` | Define atlas-guided artifact contract | S | WP-00 | contract |
| WP-02 | `L-2` | `H-1`, `T-1` | Convert atlas clusters to ontology-compatible candidate records | M | WP-01 | bridge |
| WP-03 | `L-2` | `H-1` | Build atlas thread-to-candidate lookup and coverage report | M | WP-02 | bridge |
| WP-04 | `L-3` | `T-1` | Define atlas-guided LocalAI prompt/parser contract | M | WP-03 | extraction |
| WP-05 | `L-3` | `H-2`, `T-1` | Add atlas-guided extraction mode with progressive artifacts | M | WP-04 | extraction |
| WP-06 | `L-4` | `H-3`, `T-1` | Reconcile and dedupe extracted items by canonical candidate | M | WP-05 | reconciliation |
| WP-07 | `L-5` | `H-4`, `V-1` | Add bounded snow-white wrapper and runbook for no-publish pass | S | WP-05 | ops |
| WP-08 | `T-1` | `V-1` | Cross-package focused tests and contract fixtures | M | WP-02-WP-07 | verification |
| WP-09 | `R-1` | `V-1` | Independent safety review before live run | S | WP-08 | review |
| WP-10 | `L-5` | `O-0`, `V-1` | Bounded remote smoke, no publish | S | WP-09 | live |
| WP-11 | `L-5` | `O-0`, `V-1` | Full atlas-guided extraction, no publish | L | WP-10 | live |
| WP-12 | `L-4` | `H-5`, `V-1` | Review summary and publish-readiness manifest | M | WP-11 | review |
| WP-13 | `L-5` | `O-0`, `R-1`, `V-1` | Publish-limited smoke to new wing only if review green | S | WP-12 | live |
| WP-14 | `O-0` status-only | `H-5`, `V-1` | Closure docs/devlog, commit, push | S | WP-13 or no-publish closure verdict | closure |

Parallel activation plan:

- After WP-00: activate WP-01.
- After WP-01: activate WP-02 and WP-04 design skeleton only if write scopes do not overlap; otherwise run WP-02 first.
- After WP-02: activate WP-03.
- After WP-03: activate WP-04 and WP-07 design skeleton in parallel if write scopes do not overlap.
- After WP-05: activate WP-06 and WP-08 focused test expansion in parallel.
- Live work remains serialized: WP-09, then WP-10, then WP-11, then WP-12, then optional WP-13.

---

## orchestration protocol

Workers own bounded packages. `O-0` assigns, reviews, accepts or rejects, records drift, and integrates only after evidence.

### Implementation ownership rule

Workers implement bounded packages. `O-0` assigns, reviews, accepts/rejects, records drift, and integrates only after evidence. `O-0` must not preempt worker implementation because a change appears obvious.

### Submilestone loop

1. `O-0` rereads this worksheet.
2. `O-0` activates exactly one package or a listed non-conflicting parallel package set.
3. `O-0` gives each worker explicit file/subsystem ownership and reminds them they are not alone in the codebase.
4. Worker implements within assigned write scope only.
5. Worker returns changed paths, behavior summary, tests/checks, and known gaps.
6. `O-0` reviews evidence against checkpoint requirements.
7. `R-1` or `V-1` reviews where required.
8. `O-0` records green/amber/red checkpoint verdict in worksheet/status mode.
9. Only green checkpoints unlock downstream work.

### Progress/materialization rule

The atlas-guided runner must materialize progressively:

- `progress.json` after each phase and at bounded intervals during long phases.
- One append-only JSONL per long phase.
- `artifacts_index.json` listing artifact key, schema name, relative path, phase, count, and dashboard/review safety.
- `source_file_errors.jsonl` for malformed/truncated source files.
- `atlas_candidate_coverage.json` for thread-to-candidate coverage.
- `invalid_outputs.jsonl` for invalid LocalAI responses with bounded excerpts.
- `reconciled_signals.jsonl` only after extraction artifacts are complete enough for reconciliation.
- `publish_checkpoint.jsonl` only when an explicit publish gate is open.

Progress cannot exist only in terminal output.

### Evidence rules

Acceptable evidence:

- schema tests for every new emitted artifact type
- fixture tests converting atlas `topic_clusters.jsonl` rows into candidate records
- tests proving thread-to-candidate lookup preserves all unmatched/noisy threads
- prompt tests proving LocalAI sees bounded candidate context, not the entire ontology
- parser tests for invalid JSON, unknown candidate IDs, invalid canonical wing/room, and null/no-signal cases
- fake-provider extraction tests proving no-publish defaults, progress writes, retry behavior, and resume/idempotency
- reconciliation tests proving overlap dedupe and candidate provenance preservation
- wrapper tests proving CPU/memory caps, service user, LocalAI-on-LAN, and forbidden path refusal
- read-only remote smoke evidence before any full run
- independent review proving no delete, no cloud, no old-wing mutation, no unreviewed publish, and no old-run overwrite

Insufficient evidence:

- worker summary alone
- docs saying atlas is used without artifact-level tests
- restarting the old broad prompt runner
- a prompt that lists only seed item types without atlas candidates
- candidate labels based only on stopword-prone subthread labels
- a live run that publishes before review
- a successful LocalAI call without durable artifacts
- dashboard status without checking run artifacts
- any direct `O-0` implementation outside declared mutation mode

### Milestone cadence

Each coherent package milestone requires:

- focused verification
- worksheet/status update
- devlog/docs update if branch truth changed
- commit created by `O-0` only after accepted evidence
- push to `git@github.com:botman058/mempalace.git HEAD:refs/heads/codex/mempalace-http-mcp-closure`

---

## checkpoints and gates

### Checkpoint A - Worksheet Baseline Green

- **Proves:** tranche is controlled by a saved mutation-lock worksheet.
- **Required evidence:** worksheet exists on disk; branch/head/status recorded; completed atlas run id recorded; old partial run path recorded; dirty-file scope recorded; corrected lead/helper model assignments recorded.
- **Insufficient evidence:** plan in chat only, missing mutation lock, or `gpt-5.3-codex` assigned as package lead.
- **Disposition:** green unlocks WP-01.

### Checkpoint B - Atlas-Guided Contract Green

- **Proves:** the bridge outputs are durable and inspectable before implementation spreads.
- **Required evidence:** schema tests for bridge candidate records, thread candidate lookup, coverage report, progress, artifact index, extraction records, reconciliation records, and optional publish checkpoint.
- **Insufficient evidence:** prose-only schema or terminal progress.
- **Disposition:** green unlocks WP-02 and WP-04 design skeleton.

### Checkpoint C - Atlas Bridge Green

- **Proves:** completed atlas topic clusters can become ontology-compatible candidates without LocalAI or palace writes.
- **Required evidence:** fixture tests for candidate, mixed, and noise cluster rows; stable candidate IDs; preserved representative thread refs; no LocalAI/MCP/palace calls.
- **Insufficient evidence:** using `atlas_summary.md` prose only.
- **Disposition:** green unlocks WP-03.

### Checkpoint D - Candidate Coverage Green

- **Proves:** the next mining pass knows which atlas candidates apply to each thread and which threads are unmapped.
- **Required evidence:** thread coverage report with total, candidate-mapped, noisy, mixed, and unmapped counts; tests for missing cluster refs; tests for duplicate thread refs.
- **Insufficient evidence:** candidate count without per-thread coverage.
- **Disposition:** green unlocks WP-04 and WP-05.

### Checkpoint E - Prompt/Parser Green

- **Proves:** LocalAI output is constrained by atlas candidates and cannot invent unchecked room placements silently.
- **Required evidence:** mocked LocalAI prompt/parser tests for valid candidate selection, null/no-signal, unknown candidate ID rejection, invalid canonical keys, invalid JSON, and bounded provenance.
- **Insufficient evidence:** one live model response.
- **Disposition:** green unlocks extraction mode.

### Checkpoint F - Extraction And Reconciliation Green

- **Proves:** atlas-guided extraction is resumable, no-publish by default, and dedupes overlapping windows.
- **Required evidence:** fake-provider tests; checkpoint/resume tests; invalid-output records; reconciliation/dedupe tests; candidate provenance preserved in reconciled rows.
- **Insufficient evidence:** segment extraction without final reconciliation.
- **Disposition:** green unlocks ops wrapper and cross-package verification.

### Checkpoint G - Ops Wrapper Green

- **Proves:** the live runner can execute safely on `snow-white-iii`.
- **Required evidence:** wrapper tests or static checks for service user `mempalace`, `CPUQuota=200%`, `MemoryMax=16G`, LocalAI base URL guard, no default publish, forbidden root refusal, and run-root path guard.
- **Insufficient evidence:** CLI help only.
- **Disposition:** green participates in WP-09 review.

### Checkpoint H - Cross-Package Verification Green

- **Proves:** bridge, prompt, extraction, reconciliation, and ops surfaces cohere before live operations.
- **Required evidence:** targeted suite covering WP-02 through WP-07, `py_compile`, `ruff` where scoped, shell `bash -n`, and `git diff --check`.
- **Insufficient evidence:** package-local tests only.
- **Disposition:** green unlocks independent review.

### Checkpoint I - Safety Review Green

- **Proves:** implementation cannot delete, call cloud, mutate old wings, publish by default, or overwrite diagnostic artifacts.
- **Required evidence:** independent `R-1` review with file/path evidence and explicit green/amber/red verdict.
- **Insufficient evidence:** worker self-review.
- **Disposition:** green unlocks bounded remote smoke.

### Checkpoint J - Bounded Remote Smoke Green

- **Proves:** a small atlas-guided no-publish run works on `snow-white-iii`.
- **Required evidence:** `--limit` run as `mempalace`; CPU cap `200%`; memory cap `16G`; LocalAI URL local; artifacts emitted; no palace drawer-count change in protected wings; no publish checkpoint unless publish explicitly disabled with zero rows.
- **Insufficient evidence:** local tests only.
- **Disposition:** green unlocks full no-publish extraction.

### Checkpoint K - Full No-Publish Extraction Green

- **Proves:** the complete staged archive has an atlas-guided extraction/reconciliation artifact set ready for human review.
- **Required evidence:** completed or cleanly resumable full run; segment counts; candidate coverage; invalid/error counts; reconciled signal counts; duplicate-rate summary; no publish; no old-wing mutation.
- **Insufficient evidence:** raw `chatgpt` drawer count or old `chatgpt_signals` count.
- **Disposition:** green unlocks publish-readiness review.

### Checkpoint L - Publish Readiness Green

- **Proves:** human-reviewable artifacts are good enough for a bounded publish smoke or for explicit no-publish closure.
- **Required evidence:** review summary with top canonical wings/rooms, noisy clusters, duplicate rates, type distribution, sample accepted/rejected records, and explicit publish recommendation.
- **Insufficient evidence:** model confidence alone.
- **Disposition:** green unlocks optional WP-13 publish smoke or no-publish closure.

### Checkpoint M - Publish Smoke Green

- **Proves:** reviewed atlas-guided signals can be published idempotently into the new wing only.
- **Required evidence:** tiny reviewed publish limit; target wing `chatgpt_atlas_signals`; deterministic IDs; no-op rerun; no mutation of `chatgpt`, `chatgpt_signals`, or old `chatgpt_thread_signals`.
- **Insufficient evidence:** unbounded publish or publish into old wings.
- **Disposition:** green unlocks closure.

### Checkpoint N - Closure Green

- **Proves:** branch truth, docs, and remote state are coherent.
- **Required evidence:** worksheet/devlog/docs updated, tests recorded, dirty-file scope preserved, commit created, branch pushed.
- **Insufficient evidence:** uncommitted worksheet or unstated dirty files.
- **Disposition:** tranche closed.

---

## detailed work packages

### WP-00 - Worksheet And Baseline Freeze

- **owner:** `O-0`
- **lead:** `O-0` in worksheet/status mode only
- **support:** none
- **objective:** save this worksheet with exact Tako-required structure and frozen branch/data truth.
- **why:** no implementation may start until the atlas-guided tranche is controlled by a durable O0 worksheet.
- **files/subsystems:** `docs/worksheets/mempalace_chatgpt_atlas_guided_mining_worksheet_2026-05-12.md`
- **deliverables:** saved worksheet with corrected lead/helper model assignments, branch status, atlas run id, old partial run status, package table, checkpoints, and assumptions.
- **acceptance:** Checkpoint A required evidence is present.
- **exit:** WP-01 activation.

### WP-01 - Atlas-Guided Artifact Contract

- **owner:** `O-0`
- **lead:** `L-1`
- **support:** `T-1`
- **objective:** define durable artifact contracts for the atlas-guided mining bridge and runner.
- **why:** the handoff from atlas to mining must be schema-bound before prompt or runner work starts.
- **files/subsystems:** contract module/tests and reference docs for atlas-guided artifacts.
- **deliverables:** schema/builders/validators for candidate bridge records, thread-candidate lookup, coverage report, extraction records, reconciliation records, progress, artifact index, and optional publish checkpoint.
- **acceptance:** Checkpoint B green.
- **exit:** WP-02 activation.

### WP-02 - Atlas Cluster To Candidate Bridge

- **owner:** `O-0`
- **lead:** `L-2`
- **support:** `H-1`, `T-1`
- **objective:** convert atlas `topic_clusters.jsonl` into ontology-compatible candidate cluster records.
- **why:** LocalAI should route against candidate canonical rooms derived from the atlas, not broad seed labels.
- **files/subsystems:** atlas bridge module/tests.
- **deliverables:** deterministic candidate IDs, candidate keys, examples, top terms, representative thread refs, status handling for candidate/mixed/noise clusters.
- **acceptance:** Checkpoint C green.
- **exit:** WP-03 activation.

### WP-03 - Thread Candidate Lookup And Coverage Report

- **owner:** `O-0`
- **lead:** `L-2`
- **support:** `H-1`
- **objective:** map atlas thread IDs to candidate hints and record coverage gaps.
- **why:** extraction prompts need bounded candidate context per segment/thread, and review needs to know what the atlas did not cover.
- **files/subsystems:** atlas bridge module/tests.
- **deliverables:** `atlas_thread_candidates.jsonl`, `atlas_candidate_coverage.json`, unmatched/noisy/mixed thread reporting.
- **acceptance:** Checkpoint D green.
- **exit:** WP-04 activation.

### WP-04 - Atlas-Guided Prompt And Parser Contract

- **owner:** `O-0`
- **lead:** `L-3`
- **support:** `T-1`
- **objective:** build LocalAI prompt and parser logic that constrains extracted items to atlas candidate context.
- **why:** the old prompt produced broad seed-type distributions and weak room labels; the new prompt must use atlas candidates explicitly.
- **files/subsystems:** prompt/parser helpers and tests.
- **deliverables:** prompt builder, parser, invalid-output taxonomy, unknown-candidate rejection, null/no-signal support.
- **acceptance:** Checkpoint E green.
- **exit:** WP-05 activation.

### WP-05 - Atlas-Guided Extraction Mode

- **owner:** `O-0`
- **lead:** `L-3`
- **support:** `H-2`, `T-1`
- **objective:** add a new atlas-guided no-publish extraction mode to the thread-signal runner.
- **why:** live mining must consume atlas artifacts and produce durable artifacts without publishing by default.
- **files/subsystems:** extraction runner, CLI flags, tests.
- **deliverables:** `--atlas-guided`, `--atlas-run-dir`, `--candidate-records`, no-publish default, progressive progress and checkpoints.
- **acceptance:** Checkpoint F extraction evidence green.
- **exit:** WP-06 and WP-07 activation.

### WP-06 - Candidate-Aware Reconciliation And Dedupe

- **owner:** `O-0`
- **lead:** `L-4`
- **support:** `H-3`, `T-1`
- **objective:** reconcile extracted items into candidate-aware signal records.
- **why:** overlapping segment windows and duplicate exports must not multiply identical signals.
- **files/subsystems:** reconciliation helper/tests.
- **deliverables:** `reconciled_signals.jsonl` with canonical candidate provenance, dedupe stats, duplicate examples, and publish-ready fields.
- **acceptance:** Checkpoint F reconciliation evidence green.
- **exit:** WP-08 activation.

### WP-07 - Snow-White Atlas-Guided Runner

- **owner:** `O-0`
- **lead:** `L-5`
- **support:** `H-4`, `V-1`
- **objective:** provide a safe transient-unit wrapper and runbook for atlas-guided no-publish extraction.
- **why:** full work belongs on `snow-white-iii` with bounded CPU/memory and local LocalAI.
- **files/subsystems:** systemd wrapper, ops docs, wrapper tests.
- **deliverables:** wrapper with run-root guard, service user, CPU/memory caps, LocalAI base guard, no default publish, no `/media/u0/Extreme SSD`.
- **acceptance:** Checkpoint G green.
- **exit:** WP-08 activation.

### WP-08 - Cross-Package Verification

- **owner:** `O-0`
- **lead:** `T-1`
- **support:** `V-1`
- **objective:** prove bridge, prompt/parser, extraction, reconciliation, and ops wrapper cohere.
- **why:** live LocalAI runs are costly and must not start from package-local confidence only.
- **files/subsystems:** focused tests, fixtures, static checks.
- **deliverables:** targeted test suite, fixture atlas run, shell/static verification evidence.
- **acceptance:** Checkpoint H green.
- **exit:** WP-09 activation.

### WP-09 - Independent Safety Review

- **owner:** `O-0`
- **lead:** `R-1`
- **support:** `V-1`
- **objective:** independently review implementation before any live run.
- **why:** the run touches LocalAI and may eventually publish; safety must be reviewed before remote execution.
- **files/subsystems:** all atlas-guided modules/scripts/tests/docs.
- **deliverables:** green/amber/red review with file/path evidence.
- **acceptance:** Checkpoint I green.
- **exit:** WP-10 activation.

### WP-10 - Bounded Remote Smoke

- **owner:** `O-0`
- **lead:** `L-5`
- **support:** `O-0`, `V-1`
- **objective:** run a limited atlas-guided no-publish pass on `snow-white-iii`.
- **why:** prove real paths, LocalAI behavior, service-user permissions, resource caps, and artifact writing before full run.
- **files/subsystems:** live run artifacts only.
- **deliverables:** limited run directory with progress, checkpoints, coverage, extraction, reconciliation artifacts, and no publish.
- **acceptance:** Checkpoint J green.
- **exit:** WP-11 activation.

### WP-11 - Full Atlas-Guided No-Publish Extraction

- **owner:** `O-0`
- **lead:** `L-5`
- **support:** `O-0`, `V-1`
- **objective:** run the complete atlas-guided extraction and reconciliation pass over the staged ChatGPT source archive.
- **why:** produce a reviewable signal layer before publishing anything.
- **files/subsystems:** live run artifacts only.
- **deliverables:** completed or cleanly resumable no-publish run under atlas-guided run root.
- **acceptance:** Checkpoint K green.
- **exit:** WP-12 activation.

### WP-12 - Review Summary And Publish Readiness

- **owner:** `O-0`
- **lead:** `L-4`
- **support:** `H-5`, `V-1`
- **objective:** summarize output quality and decide whether a bounded publish smoke is justified.
- **why:** publishing should be a reviewed decision based on candidate quality, duplicate rate, noisy clusters, and samples.
- **files/subsystems:** report generator/docs, live artifact review.
- **deliverables:** review summary, publish readiness manifest, explicit green/amber/red recommendation.
- **acceptance:** Checkpoint L green.
- **exit:** WP-13 publish smoke or no-publish closure.

### WP-13 - Publish-Limited Smoke

- **owner:** `O-0`
- **lead:** `L-5`
- **support:** `O-0`, `R-1`, `V-1`
- **objective:** publish a tiny reviewed sample into `chatgpt_atlas_signals` only if WP-12 recommends it.
- **why:** prove idempotent write path before any wider materialization.
- **files/subsystems:** live publish artifacts only.
- **deliverables:** publish checkpoint, before/after wing counts, no-op rerun evidence.
- **acceptance:** Checkpoint M green.
- **exit:** WP-14 activation.

### WP-14 - Closure, Docs, Commit, Push

- **owner:** `O-0`
- **lead:** `O-0` in worksheet/status and integration mode only
- **support:** `H-5`, `V-1`
- **objective:** record final truth, update docs/devlog, commit and push.
- **why:** preserve durable handoff and branch state.
- **files/subsystems:** worksheet, devlog/docs only unless accepted integration requires more.
- **deliverables:** updated worksheet, docs/devlog summary, test/run evidence, commit, push.
- **acceptance:** Checkpoint N green.
- **exit:** tranche closed.

---

## assumptions

- The completed atlas run `atlas_full2_20260512T0412Z_2fc8ac5` is the canonical atlas input.
- The old partial thread-signal run is diagnostic-only and must not be resumed for production.
- The first atlas-guided full run publishes nothing.
- A later publish, if approved, targets `chatgpt_atlas_signals`, not `chatgpt`, `chatgpt_signals`, or existing `chatgpt_thread_signals`.
- `qwen3-vl-8b-instruct` is the default LocalAI model unless a no-write model smoke proves another local model is stable on production prompts.
- Existing ontology helper modules are reusable, but this tranche must not assume the ontology CLI already consumes atlas artifacts.
- The dashboard is read-only during active runs and must not call heavy MCP tools if telemetry-only mode is forced.
- No source files, run artifacts, or palace data are deleted by this tranche.

---

## checkpoint ledger

| Checkpoint | Status | Evidence | Next gate |
|---|---|---|---|
| A - Worksheet Baseline | green | Worksheet saved at `docs/worksheets/mempalace_chatgpt_atlas_guided_mining_worksheet_2026-05-12.md`; branch/head/status, atlas run, old diagnostic run, dirty scope, and corrected model-role assignments recorded. | WP-01 |
| B - Atlas-Guided Contract | green | `L-1R2` repaired candidate/mixed/noise bridge semantics and publish-checkpoint gating; `V-1` repair verification returned green; targeted tests, ruff, py_compile, and diff check passed. | WP-02 unlocked after this milestone commit/push |
| C - Atlas Bridge | green | `L-2` bridge patch accepted; combined contract+bridge tests, ruff, py_compile, diff check, and `V-1` verification passed. | WP-03 unlocked after this milestone commit/push |
| D - Candidate Coverage | green | `L-2R` coverage patch accepted; targeted and combined tests, ruff, py_compile, diff check, and `V-1` verification passed. | WP-04 unlocked after this milestone commit/push |
| E - Prompt/Parser | green | `L-3` prompt/parser patch accepted after `L-3R` repaired the forbidden output-key blocker; targeted and combined tests, ruff, py_compile, diff check, and `V-1R2` no-edit verification passed. | WP-05 unlocked after this milestone commit/push |
| F - Extraction And Reconciliation | green | WP-05 extraction mode and WP-06 reconciliation/dedupe are accepted; combined tests, ruff, py_compile, diff check, and `V-1F` no-edit verification passed. | WP-08 cross-package verification after WP-07 milestone commit/push |
| G - Ops Wrapper | green | WP-07 snow-white wrapper/runbook accepted; bash syntax, static wrapper tests, ruff, py_compile, diff check, and `V-1G` no-edit verification passed. | WP-08 cross-package verification |
| H - Cross-Package Verification | green | `T-1` returned green, `V-1H` found an amber direct-CLI LocalAI URL gap, `L-3R4` repaired strict atlas-guided snow-white allowlisting, O-0 checks passed, and `V-1H2` returned green with 115 tests passing plus ruff, py_compile, bash syntax, and diff checks. | WP-09 unlocked after this milestone commit/push |
| I - Safety Review | green | `R-1` returned red on direct atlas-guided CLI run-dir confinement; `L-3R5` and `L-5R` repairs landed; O-0 checks passed with 118 tests plus ruff, py_compile, bash syntax, and diff checks; `R-1R` returned green and `V-1I2` found no red issues. | WP-10 unlocked after this milestone commit/push |
| J - Bounded Remote Smoke | green | `L-5R2` promoted committed app `73285d6` without deletes/restarts, materialized guided inputs, and completed bounded wrapper run `wp10smoke20260513t025130z`; `V-1J` independently verified complete/no-publish artifacts and resource caps. | WP-11 unlocked after this milestone commit/push |
| K - Full No-Publish Extraction | active | WP-11 activated on 2026-05-13 after WP-10 milestone commit `e7dc898` was pushed. | WP-12 after green verdict |
| L - Publish Readiness | blocked | Waiting on WP-12. | WP-13 or no-publish closure |
| M - Publish Smoke | blocked | Optional; waiting on WP-13 activation and explicit review recommendation. | WP-14 after green verdict |
| N - Closure | blocked | Waiting on final docs/devlog/tests/run evidence and commit/push. | Tranche closed |

---

## package status ledger

| Package | Status | Owner/lead | Notes |
|---|---|---|---|
| WP-00 | complete | `O-0` | Worksheet and baseline freeze are complete; Checkpoint A is green. |
| WP-01 | complete | `L-1R2` | Artifact contract accepted at Checkpoint B after repair and independent green verification. |
| WP-02 | complete | `L-2` | Atlas cluster-to-candidate bridge accepted at Checkpoint C. |
| WP-03 | complete | `L-2R` | Thread candidate lookup and coverage report accepted at Checkpoint D. |
| WP-04 | complete | `L-3` / `L-3R` | Atlas-guided LocalAI prompt/parser contract accepted at Checkpoint E after repair and independent green verification. |
| WP-05 | complete | `L-3` / `L-3R2` | Atlas-guided no-publish extraction mode accepted after repair and independent green verification. |
| WP-06 | complete | `L-4` | Candidate-aware reconciliation accepted after repair and independent green verification. |
| WP-07 | complete | `L-5` | Snow-white atlas-guided no-publish wrapper accepted after independent green verification. |
| WP-08 | complete | `T-1` / `L-3R4` | Cross-package verification accepted after amber direct-CLI LocalAI URL repair and independent green re-verification. |
| WP-09 | complete | `R-1` / `L-3R5` / `L-5R` | Safety review accepted after red/amber repairs, O-0 verification, and independent green re-review. |
| WP-10 | complete | `L-5` / `L-2R3` | Bounded no-publish smoke accepted after materialization repair, live promotion, successful wrapper run, and independent artifact verification. |
| WP-11 | active | `L-5` | Full atlas-guided no-publish extraction activated; must run through the snow-white wrapper as `mempalace`, with no publish, no cloud calls, no deletes, no `/media/u0/Extreme SSD`, and resource caps intact. |
| WP-12 | blocked | `L-4` | Publish-readiness review only after full no-publish artifacts exist. |
| WP-13 | blocked | `L-5` | Optional tiny publish smoke only after explicit green recommendation. |
| WP-14 | blocked | `O-0` | Closure docs/devlog/commit/push after publish smoke or explicit no-publish closure. |

---

## drift ledger

| Date | Status | Drift item | Disposition |
|---|---|---|---|
| 2026-05-12 | closed | Initial WP-00 worksheet draft omitted explicit checkpoint/package/drift/decision ledger sections. | Recovered in worksheet/status mode before the second WP-00 evidence commit; no implementation package was activated and no code was touched. |
| 2026-05-12 | closed | WP-01 support helper `T-1` exhausted context before returning evidence. | Evidence discarded; no files landed from that lane. |
| 2026-05-12 | closed | Original WP-01 lead `L-1` stalled without returning files or evidence. | Lane was closed and WP-01 reassigned to bounded replacement lead `L-1R`; no implementation files had landed before reassignment. |
| 2026-05-12 | closed | `V-1` found WP-01 amber blockers: candidate bridge rows force canonical room identity for `noise` rows, tests do not cover mixed/noise bridge semantics, and publish checkpoint cannot represent explicit future `chatgpt_atlas_signals` gate. | Repaired by `L-1R2`; follow-up `V-1` verification returned green and Checkpoint B is green. |
| 2026-05-12 | closed | `V-1` found a WP-04 amber blocker: model outputs containing `localai_base_url` or related control keys could still be accepted. | Repaired by `L-3R` with recursive forbidden-key rejection and regression tests; `V-1R2` returned green. |
| 2026-05-12 | closed | `V-1R` initially returned environment-amber because it used ambient `pytest`/`ruff` instead of the repo venv. | Replaced with `V-1R2` using explicit `.venv/bin/...` commands; no functional blocker remained. |
| 2026-05-12 | closed | O-0 review found WP-05 amber risks: required atlas JSONL inputs could be silently tolerated through the generic reader, and implicit atlas-guided runs wrote directly to the run-root instead of a `<run_id>` child. | Repaired by `L-3R2`; strict atlas input loading now fails before provider calls, checkpoint readers remain tolerant, and implicit atlas run dirs use a deterministic child under the canonical root. |
| 2026-05-12 | closed | O-0 review found a WP-06 amber issue: reconciliation candidate provenance was nested only under `candidate_metadata`, making candidate identity less directly inspectable in review artifacts. | Repaired by `L-4`; reconciliation provenance now includes direct `candidate_id`, `candidate_key`, `canonical_wing`, `canonical_room`, `atlas_candidate_ids`, and `atlas_candidate_keys` fields while preserving nested metadata. |
| 2026-05-12 | closed | `V-1H` found a WP-08 amber blocker: direct `--atlas-guided` CLI runs used the legacy LocalAI blocklist guard instead of the snow-white-only allowlist enforced by the systemd wrapper. | Repaired by `L-3R4`; direct atlas-guided runs now require `http://snow-white-iii:8080/v1` or `http://snow-white-iii.local:8080/v1` before provider creation, while legacy localhost behavior remains unchanged. `V-1H2` returned green. |
| 2026-05-12 | closed | `R-1` returned WP-09 red: direct atlas-guided CLI can accept arbitrary `--run-dir` or env run dirs and overwrite existing diagnostic artifacts. `V-1` independently found this amber. | Repaired by `L-3R5`; explicit/env atlas-guided CLI run dirs must resolve to child directories under the canonical guided run root and must not use `/media/u0/Extreme SSD`. O-0 verification passed and `R-1R` returned green. |
| 2026-05-12 | closed | `V-1` and `R-1` found wrapper host-guard amber: `MEMPALACE_INSTALL_ALLOW_OTHER_HOST=1` bypasses the snow-white host check. | Repaired by `L-5R`; the live wrapper now refuses any host other than `snow-white-iii` or `snow-white-iii.local`, and the static test asserts the bypass variable is absent. O-0 verification passed and `R-1R` returned green. |
| 2026-05-12 | closed | WP-10 bounded smoke failed before `systemd-run`: canonical atlas run `atlas_full2_20260512T0412Z_2fc8ac5` has `topic_clusters.jsonl` and `thread_index.jsonl`, but lacks the guided candidate artifacts required by the wrapper. | Repaired by `L-2R3` with `scripts/materialize_chatgpt_atlas_guided_inputs.py`, focused tests, README updates, and changelog entry. O-0 verification passed; rerun pending after commit/push/promote/materialization. |
| 2026-05-12 | monitored | Parallel activation notes conflict: the overview table blocks WP-08 on WP-02 through WP-07, while one activation-plan bullet says to activate WP-08 after WP-05. | Follow the detailed package dependencies and WP-05 exit: activate WP-06 and WP-07; keep WP-08 blocked until WP-06/WP-07 evidence exists. |
| 2026-05-12 | monitored | Modified `.agents/plugins/marketplace.json` is present in the worktree but out of scope. | Must remain unstaged and unmodified by this tranche unless user explicitly changes scope. |
| 2026-05-12 | monitored | Untracked `docs/reference/` is present but unaccepted. | Must remain unstaged and unrevised by this tranche until a package explicitly owns it. |

---

## decision ledger

| Date | Decision | Rationale | Consequence |
|---|---|---|---|
| 2026-05-12 | Use `atlas_full2_20260512T0412Z_2fc8ac5` as canonical atlas input. | It is the completed pre-LLM atlas run with recorded thread/topic artifacts and no drawer publication. | WP-02/WP-03 consume atlas artifacts instead of old broad LocalAI classifications. |
| 2026-05-12 | First atlas-guided extraction is no-publish. | Output quality must be inspected before palace mutation. | WP-10/WP-11 produce durable artifacts only; publish remains blocked. |
| 2026-05-12 | Any later publish targets `chatgpt_atlas_signals`. | Existing `chatgpt`, `chatgpt_signals`, and partial `chatgpt_thread_signals` must remain protected. | Publish smoke cannot write to old wings. |
| 2026-05-12 | `gpt-5.3-codex` and `gpt-5.3-codex-spark` are helpers, not leads. | User explicitly rejected low/medium-depth lead assignment for architecture ownership. | Lead roles use `gpt-5.5 high` or `gpt-5.4 high`; bounded helpers use smaller models. |
| 2026-05-12 | Checkpoint B is the active hard gate. | Artifact contracts must precede runner/prompt/live work. | WP-01 is the only unlocked implementation package after WP-00. |
| 2026-05-12 | Defer WP-04 design skeleton until WP-02/WP-03 bridge shape is accepted. | The worksheet allowed WP-04 design skeleton after WP-01 only if write scopes do not overlap; the prompt/parser contract depends on exact bridge/coverage record semantics. | Activate WP-02 next; keep WP-04 blocked until bridge evidence is available. |
| 2026-05-12 | WP-04 parser rejects forbidden control keys by JSON key, not by scanning free-text values. | The model may legitimately mention LocalAI, MCP, URLs, or paths in grounded text; the unsafe path is structured control/config output that could steer tools or writes. | Reject `localai*`, `chroma*`, `mcp*`, `network*`, `provider*`, `vector*`, `tool*`, `publish*`, `palace*`, `drawer*`, `write*`, URL/path/root-style keys anywhere in model JSON. |
| 2026-05-12 | Implicit atlas-guided extraction runs use a deterministic child under the canonical atlas-guided run root. | The worksheet requires artifacts under `/media/u0/OneDrive_Backup/mempalace/data/atlas_guided_chatgpt_signals/<run_id>/`, while resumability requires stable paths rather than timestamp-only run directories. | `--atlas-guided` without explicit `--run-dir` derives a child from `--atlas-run-dir`; explicit run dirs remain operator-owned. |
| 2026-05-12 | WP-06 and WP-07 run in parallel after WP-05; WP-08 stays blocked. | Reconciliation and ops wrapper write scopes are disjoint, but cross-package verification depends on both. | `L-4` owns reconciliation, `L-5` owns wrapper/runbook, helpers are assigned read-only or scoped test work. |
| 2026-05-12 | Atlas reconciliation emits explicit duplicate rows as well as accepted rows. | Review needs visibility into dedupe decisions instead of silently collapsing all duplicates. | `reconciled_signals.jsonl` may contain `accepted` and `duplicate` reconciliation statuses; publish remains blocked until later review gates. |

---

## execution log

### 2026-05-12 - WP-01 Activation

- `O-0` reread this worksheet before package activation.
- Current gate: Checkpoint B.
- Activated package: WP-01 only.
- Assigned `L-1` as contract lead using `gpt-5.5` high.
- Assigned `T-1` as focused test helper using `gpt-5.3-codex-spark` high.
- Write scope is limited to the atlas-guided artifact contract module/tests/docs selected by WP-01.
- WP-02 through WP-14 remain blocked.
- `T-1` errored due to context exhaustion before returning evidence; no `T-1` work was accepted.
- Original `L-1` stalled without landing files and was closed.
- WP-01 was reassigned to replacement lead `L-1R` using `gpt-5.5` high with narrowed write scope: `mempalace/chatgpt_atlas_guided_contract.py` and `tests/test_chatgpt_atlas_guided_contract.py`.
- `L-1R` returned a bounded patch in `mempalace/chatgpt_atlas_guided_contract.py` and `tests/test_chatgpt_atlas_guided_contract.py`.
- `O-0` ran `.venv/bin/pytest tests/test_chatgpt_atlas_guided_contract.py`: passed, `31 passed`.
- `O-0` ran `.venv/bin/ruff check mempalace/chatgpt_atlas_guided_contract.py tests/test_chatgpt_atlas_guided_contract.py`: passed.
- `O-0` ran `git diff --check -- mempalace/chatgpt_atlas_guided_contract.py tests/test_chatgpt_atlas_guided_contract.py docs/worksheets/mempalace_chatgpt_atlas_guided_mining_worksheet_2026-05-12.md`: passed.
- `V-1` independent no-edit review returned amber, not green.
- Checkpoint B remains amber because candidate bridge rows cannot represent `noise` rows without canonical room identity and publish checkpoints cannot encode future explicit `chatgpt_atlas_signals` gate evidence.
- WP-01 repair assigned to replacement lead `L-1R2` using `gpt-5.5` high with the same bounded write scope.
- `L-1R2` repaired the contract so candidate bridge rows support `candidate`, `mixed`, and `noise`; `noise` rows preserve atlas evidence without candidate/canonical identity; `mixed` rows are either unresolved or complete candidate-backed; and publish checkpoint rows can encode an explicit approved/open gate only for `chatgpt_atlas_signals`.
- `O-0` ran `.venv/bin/pytest tests/test_chatgpt_atlas_guided_contract.py`: passed, `33 passed`.
- `O-0` ran `.venv/bin/ruff check mempalace/chatgpt_atlas_guided_contract.py tests/test_chatgpt_atlas_guided_contract.py`: passed.
- `O-0` ran `.venv/bin/python -m py_compile mempalace/chatgpt_atlas_guided_contract.py tests/test_chatgpt_atlas_guided_contract.py`: passed.
- `O-0` ran `git diff --check -- mempalace/chatgpt_atlas_guided_contract.py tests/test_chatgpt_atlas_guided_contract.py docs/worksheets/mempalace_chatgpt_atlas_guided_mining_worksheet_2026-05-12.md`: passed.
- `V-1` repair verifier returned green with file/line evidence for candidate/mixed/noise semantics, publish checkpoint gating, and forbidden LocalAI/MCP/Chroma/palace-write fields.
- Checkpoint B verdict: green.
- Checkpoint B disposition: WP-02 is unlocked after this milestone is committed and pushed. WP-04 design skeleton is deferred until WP-02/WP-03 bridge shape is accepted.
- `git commit -m "Add atlas-guided mining contract"` created milestone commit `e3a4748`.
- `git push git@github.com:botman058/mempalace.git HEAD:refs/heads/codex/mempalace-http-mcp-closure` pushed `e3a4748` to the fork branch.
- Out-of-scope dirty `.agents/plugins/marketplace.json` and untracked `docs/reference/` remained unstaged.

### 2026-05-12 - WP-02 Activation

- `O-0` reread this worksheet before package activation.
- Current gate: Checkpoint C.
- Activated package: WP-02 only.
- Assigned `L-2` as atlas bridge lead using `gpt-5.4` high.
- Assigned `H-1` as bounded implementation helper using `gpt-5.3-codex` medium.
- Assigned `T-1` as focused test helper using `gpt-5.3-codex-spark` high.
- WP-03 through WP-14 remain blocked.
- `T-1` support spawn was not available because the agent thread limit was reached; no `T-1` evidence was used for WP-02.
- `H-1` completed a read-only fixture/edge-case brief for atlas `topic_clusters.jsonl` rows and bridge mapping expectations.
- `L-2` implemented `mempalace/chatgpt_atlas_guided_bridge.py` and `tests/test_chatgpt_atlas_guided_bridge.py`.
- `O-0` ran `.venv/bin/pytest tests/test_chatgpt_atlas_guided_bridge.py`: passed, `7 passed`.
- `O-0` ran `.venv/bin/pytest tests/test_chatgpt_atlas_guided_contract.py tests/test_chatgpt_atlas_guided_bridge.py`: passed, `40 passed`.
- `O-0` ran `.venv/bin/ruff check mempalace/chatgpt_atlas_guided_contract.py mempalace/chatgpt_atlas_guided_bridge.py tests/test_chatgpt_atlas_guided_contract.py tests/test_chatgpt_atlas_guided_bridge.py`: passed.
- `O-0` ran `.venv/bin/python -m py_compile mempalace/chatgpt_atlas_guided_contract.py mempalace/chatgpt_atlas_guided_bridge.py tests/test_chatgpt_atlas_guided_contract.py tests/test_chatgpt_atlas_guided_bridge.py`: passed.
- `O-0` ran `git diff --check -- mempalace/chatgpt_atlas_guided_bridge.py tests/test_chatgpt_atlas_guided_bridge.py`: passed.
- `V-1` no-edit verification returned green for pure/no external side effects, atlas topic-cluster row validation, candidate bridge contract emission, candidate/mixed/noise handling, deterministic keys/IDs, preserved evidence fields, and focused tests.
- Checkpoint C verdict: green.
- Checkpoint C disposition: WP-03 is unlocked after this milestone is committed and pushed.
- `git commit -m "Add atlas-guided cluster bridge"` created milestone commit `a2eeda3`.
- `git push git@github.com:botman058/mempalace.git HEAD:refs/heads/codex/mempalace-http-mcp-closure` pushed `a2eeda3` to the fork branch.
- Out-of-scope dirty `.agents/plugins/marketplace.json` and untracked `docs/reference/` remained unstaged.

### 2026-05-12 - WP-03 Activation

- `O-0` reread this worksheet before package activation.
- Current gate: Checkpoint D.
- Activated package: WP-03 only.
- Assigned replacement `L-2R` as atlas coverage lead using `gpt-5.4` high.
- Assigned `H-1R` as bounded implementation helper using `gpt-5.3-codex` medium.
- WP-04 through WP-14 remain blocked.
- `H-1R` completed a read-only checklist for thread-index fields, source refs, duplicate/missing thread-ref shapes, and coverage math.
- `L-2R` implemented `mempalace/chatgpt_atlas_guided_coverage.py` and `tests/test_chatgpt_atlas_guided_coverage.py`.
- `O-0` ran `.venv/bin/pytest tests/test_chatgpt_atlas_guided_coverage.py`: passed, `6 passed`.
- `O-0` ran `.venv/bin/pytest tests/test_chatgpt_atlas_guided_contract.py tests/test_chatgpt_atlas_guided_bridge.py tests/test_chatgpt_atlas_guided_coverage.py`: passed, `46 passed`.
- `O-0` ran `.venv/bin/ruff check mempalace/chatgpt_atlas_guided_contract.py mempalace/chatgpt_atlas_guided_bridge.py mempalace/chatgpt_atlas_guided_coverage.py tests/test_chatgpt_atlas_guided_contract.py tests/test_chatgpt_atlas_guided_bridge.py tests/test_chatgpt_atlas_guided_coverage.py`: passed.
- `O-0` ran `.venv/bin/python -m py_compile mempalace/chatgpt_atlas_guided_contract.py mempalace/chatgpt_atlas_guided_bridge.py mempalace/chatgpt_atlas_guided_coverage.py tests/test_chatgpt_atlas_guided_contract.py tests/test_chatgpt_atlas_guided_bridge.py tests/test_chatgpt_atlas_guided_coverage.py`: passed.
- `O-0` ran `git diff --check -- mempalace/chatgpt_atlas_guided_coverage.py tests/test_chatgpt_atlas_guided_coverage.py`: passed.
- `V-1` no-edit verification returned green for pure/no external writes, validated inputs, lookup/report schema emission, one row per thread-index row, mapped/mixed/noise/unmapped behavior, duplicate/missing refs, exact coverage math, and aligned tests.
- Checkpoint D verdict: green.
- Checkpoint D disposition: WP-04 is unlocked after this milestone is committed and pushed.
- `git commit -m "Add atlas-guided coverage mapping"` created milestone commit `a971c73`.
- `git push git@github.com:botman058/mempalace.git HEAD:refs/heads/codex/mempalace-http-mcp-closure` pushed `a971c73` to the fork branch.
- Out-of-scope dirty `.agents/plugins/marketplace.json` and untracked `docs/reference/` remained unstaged.

### 2026-05-12 - WP-04 Activation

- `O-0` reread this worksheet before package activation.
- Current gate: Checkpoint E.
- Activated package: WP-04 only.
- Assigned `L-3` as extraction prompt lead using `gpt-5.4` high.
- Assigned `T-1R` as focused parser/test helper using `gpt-5.3-codex-spark` high if agent capacity permits.
- WP-05 through WP-14 remain blocked.
- `T-1R` returned a read-only acceptance checklist covering shortlist-only prompt scope, valid candidate selection, null/no-signal, unknown candidate rejection, canonical mismatch rejection, invalid JSON, publish-control rejection, bounded provenance, and regression coverage.
- `L-3` implemented `mempalace/chatgpt_atlas_guided_prompt.py` and `tests/test_chatgpt_atlas_guided_prompt.py`.
- `L-3` delivered a pure-stdlib prompt/parser contract: prompts include bounded segment text and thread-relevant candidate shortlist only; parser emits contract-backed `accepted`, `null_signal`, and durable `invalid_output` extraction records; invalid JSON, unknown candidate IDs/keys, candidate ID/key mismatch, invalid canonical fields, missing accepted fields, bad confidence, and publish attempts fail closed.
- `O-0` ran `.venv/bin/pytest tests/test_chatgpt_atlas_guided_prompt.py`: passed, `13 passed`.
- `O-0` ran `.venv/bin/pytest tests/test_chatgpt_atlas_guided_contract.py tests/test_chatgpt_atlas_guided_bridge.py tests/test_chatgpt_atlas_guided_coverage.py tests/test_chatgpt_atlas_guided_prompt.py`: passed, `59 passed`.
- `O-0` ran `.venv/bin/ruff check mempalace/chatgpt_atlas_guided_contract.py mempalace/chatgpt_atlas_guided_bridge.py mempalace/chatgpt_atlas_guided_coverage.py mempalace/chatgpt_atlas_guided_prompt.py tests/test_chatgpt_atlas_guided_contract.py tests/test_chatgpt_atlas_guided_bridge.py tests/test_chatgpt_atlas_guided_coverage.py tests/test_chatgpt_atlas_guided_prompt.py`: passed.
- `O-0` ran `.venv/bin/python -m py_compile mempalace/chatgpt_atlas_guided_contract.py mempalace/chatgpt_atlas_guided_bridge.py mempalace/chatgpt_atlas_guided_coverage.py mempalace/chatgpt_atlas_guided_prompt.py tests/test_chatgpt_atlas_guided_contract.py tests/test_chatgpt_atlas_guided_bridge.py tests/test_chatgpt_atlas_guided_coverage.py tests/test_chatgpt_atlas_guided_prompt.py`: passed.
- `O-0` ran `git diff --check -- mempalace/chatgpt_atlas_guided_prompt.py tests/test_chatgpt_atlas_guided_prompt.py docs/worksheets/mempalace_chatgpt_atlas_guided_mining_worksheet_2026-05-12.md CHANGELOG.md`: passed.
- `V-1` no-edit verification returned amber: most Checkpoint E requirements passed, but model output containing `localai_base_url` was still accepted.
- WP-04 repair was assigned to `L-3R` using `gpt-5.4` high with the same bounded write scope.
- `L-3R` repaired the forbidden-output gate so structured control/provider/network/vector/tool/publish/palace/write/path-style keys are rejected recursively anywhere in model JSON while preserving the existing invalid-output `publish_attempt` path.
- `L-3R` added regression coverage for `localai_base_url`, `localai_model`, `chroma_collection`, `mcp`, `mcp_tool`, `network_url`, `palace_root`, `palace_write_path`, `drawer_write_path`, `write_drawer`, `publish_enabled`, and `target_wing`.
- `O-0` ran `.venv/bin/pytest tests/test_chatgpt_atlas_guided_prompt.py`: passed, `25 passed`.
- `O-0` ran `.venv/bin/pytest tests/test_chatgpt_atlas_guided_contract.py tests/test_chatgpt_atlas_guided_bridge.py tests/test_chatgpt_atlas_guided_coverage.py tests/test_chatgpt_atlas_guided_prompt.py`: passed, `71 passed`.
- `O-0` ran `.venv/bin/ruff check mempalace/chatgpt_atlas_guided_contract.py mempalace/chatgpt_atlas_guided_bridge.py mempalace/chatgpt_atlas_guided_coverage.py mempalace/chatgpt_atlas_guided_prompt.py tests/test_chatgpt_atlas_guided_contract.py tests/test_chatgpt_atlas_guided_bridge.py tests/test_chatgpt_atlas_guided_coverage.py tests/test_chatgpt_atlas_guided_prompt.py`: passed.
- `O-0` ran `.venv/bin/python -m py_compile mempalace/chatgpt_atlas_guided_contract.py mempalace/chatgpt_atlas_guided_bridge.py mempalace/chatgpt_atlas_guided_coverage.py mempalace/chatgpt_atlas_guided_prompt.py tests/test_chatgpt_atlas_guided_contract.py tests/test_chatgpt_atlas_guided_bridge.py tests/test_chatgpt_atlas_guided_coverage.py tests/test_chatgpt_atlas_guided_prompt.py`: passed.
- `V-1R` returned functional green evidence but command-runner amber because it used ambient Python tooling rather than the repo venv.
- `V-1R2` no-edit verification used explicit `.venv/bin/...` commands and returned green: `25 passed`, ruff passed, py_compile passed, diff check passed, and no network/LocalAI/MCP/Chroma/service calls were run.
- Checkpoint E verdict: green.
- Checkpoint E disposition: WP-05 is unlocked after this milestone is committed and pushed.
- `git commit -m "Add atlas-guided prompt parser"` created milestone commit `ee6dbac`.
- `git push git@github.com:botman058/mempalace.git HEAD:refs/heads/codex/mempalace-http-mcp-closure` pushed `ee6dbac` to the fork branch.
- Out-of-scope dirty `.agents/plugins/marketplace.json` and untracked `docs/reference/` remained unstaged.

### 2026-05-12 - WP-05 Activation

- `O-0` reread this worksheet before package activation.
- Current gate: Checkpoint F.
- Activated package: WP-05 only.
- Assigned `L-3` as extraction-mode lead using `gpt-5.4` high.
- Assigned `H-2` as bounded runner plumbing helper using `gpt-5.3-codex` medium if agent capacity permits.
- Assigned `T-1` as focused fake-provider/checkpoint test helper using `gpt-5.3-codex-spark` high if agent capacity permits.
- WP-06 through WP-14 remain blocked.
- WP-05 write scope is limited to the thread-signal extraction runner, atlas-guided artifact plumbing, and focused tests needed for `--atlas-guided`, `--atlas-run-dir`, `--candidate-records`, no-publish defaults, progressive artifacts, retry/idempotency, and resume behavior.
- WP-05 must not call LocalAI in tests, publish drawers, mutate existing `chatgpt`, `chatgpt_signals`, or `chatgpt_thread_signals`, or touch `.agents/plugins/marketplace.json` or `docs/reference/`.
- `H-2` completed a read-only implementation brief identifying the segment-to-atlas thread lookup risk and recommended deterministic mapping policy.
- `L-3` implemented atlas-guided extraction mode in `scripts/localai_chatgpt_thread_signals.py`.
- `T-1` implemented fake-provider and resume/idempotency coverage in `tests/test_localai_chatgpt_thread_signals.py`.
- `L-3R` repaired the first O-0 amber blocker by removing a test-only fake-provider output drain from production code and restoring the strict `--candidate-records` contract as a candidate-bridge override.
- `O-0` ran `.venv/bin/pytest --noconftest -q tests/test_localai_chatgpt_thread_signals.py`: passed, `27 passed`.
- `O-0` ran `.venv/bin/pytest tests/test_localai_chatgpt_thread_signals.py`: passed, `27 passed`.
- `O-0` ran `.venv/bin/ruff check scripts/localai_chatgpt_thread_signals.py tests/test_localai_chatgpt_thread_signals.py`: passed.
- `O-0` ran `.venv/bin/python -m py_compile scripts/localai_chatgpt_thread_signals.py tests/test_localai_chatgpt_thread_signals.py`: passed.
- `O-0` ran `git diff --check -- scripts/localai_chatgpt_thread_signals.py tests/test_localai_chatgpt_thread_signals.py`: passed.
- `O-0` review found a second amber blocker: required atlas JSONL inputs used tolerant loading and implicit atlas-guided runs could write directly to the run-root.
- `L-3R2` repaired strict atlas-input loading, moved atlas input loading before provider setup, preserved tolerant checkpoint/resume loading, and made implicit atlas-guided run dirs land under the canonical root with a deterministic child.
- `O-0` ran `.venv/bin/pytest --noconftest -q tests/test_localai_chatgpt_thread_signals.py`: passed, `30 passed`.
- `O-0` ran `.venv/bin/pytest tests/test_chatgpt_atlas_guided_contract.py tests/test_chatgpt_atlas_guided_bridge.py tests/test_chatgpt_atlas_guided_coverage.py tests/test_chatgpt_atlas_guided_prompt.py tests/test_localai_chatgpt_thread_signals.py`: passed, `101 passed`.
- `O-0` ran `.venv/bin/ruff check scripts/localai_chatgpt_thread_signals.py tests/test_localai_chatgpt_thread_signals.py mempalace/chatgpt_atlas_guided_contract.py mempalace/chatgpt_atlas_guided_bridge.py mempalace/chatgpt_atlas_guided_coverage.py mempalace/chatgpt_atlas_guided_prompt.py`: passed.
- `O-0` ran `.venv/bin/python -m py_compile scripts/localai_chatgpt_thread_signals.py tests/test_localai_chatgpt_thread_signals.py mempalace/chatgpt_atlas_guided_contract.py mempalace/chatgpt_atlas_guided_bridge.py mempalace/chatgpt_atlas_guided_coverage.py mempalace/chatgpt_atlas_guided_prompt.py`: passed.
- `O-0` ran `git diff --check -- scripts/localai_chatgpt_thread_signals.py tests/test_localai_chatgpt_thread_signals.py`: passed.
- `V-1` no-edit verification returned green for flags, legacy preservation, no-publish refusal, disabled publish checkpoint, strict atlas-input loading before provider calls, canonical default run-root child behavior, durable extraction artifacts/checkpoints, fake-provider coverage, and no delete/cloud/LocalAI/MCP test paths.
- WP-05 extraction verdict: green.
- Checkpoint F remains active because WP-06 reconciliation/dedupe evidence is still required before the full extraction-and-reconciliation gate can close.
- `git commit -m "Add atlas-guided extraction mode"` created milestone commit `6e36e3c`.
- `git push git@github.com:botman058/mempalace.git HEAD:refs/heads/codex/mempalace-http-mcp-closure` pushed `6e36e3c` to the fork branch.
- Out-of-scope dirty `.agents/plugins/marketplace.json` and untracked `docs/reference/` remained unstaged.

### 2026-05-12 - WP-06 And WP-07 Activation

- `O-0` reread this worksheet before package activation.
- Current gates: Checkpoint F for WP-06 reconciliation and Checkpoint G for WP-07 ops wrapper.
- Activated package set: WP-06 and WP-07 in parallel because their write scopes are disjoint.
- WP-08 remains blocked until WP-06 and WP-07 evidence exists.
- Assigned `L-4` as reconciliation lead using `gpt-5.4` high; agent `019e1efb-7775-7c92-b29b-d44d041c0141` / Huygens.
- Assigned `H-3` as read-only reconciliation helper using `gpt-5.3-codex` medium; agent `019e1efb-7a16-70c1-b7c3-68e3e9fa6594` / Lagrange the 2nd.
- Assigned `T-1` as focused reconciliation test helper using `gpt-5.3-codex-spark` high; agent `019e1efb-7e69-78f0-a36e-490ef13ec09b` / Pasteur the 2nd.
- Assigned `L-5` as ops wrapper lead using `gpt-5.4` high; agent `019e1efb-836d-7670-bb8e-eac3bb68b58b` / Confucius the 2nd.
- Assigned `H-4` as read-only ops helper using `gpt-5.3-codex` medium; agent `019e1efb-8a53-7940-9972-208c2fd03a83` / Planck the 2nd.
- WP-06 write scope is limited to candidate-aware reconciliation helpers, focused tests, and minimal atlas-runner integration needed to materialize `reconciled_signals.jsonl` without publishing.
- WP-07 write scope is limited to a snow-white-iii atlas-guided extraction wrapper, static wrapper tests, and `scripts/systemd/README.md`.
- WP-06 and WP-07 must not call LocalAI in tests, publish drawers, mutate existing `chatgpt`, `chatgpt_signals`, or `chatgpt_thread_signals`, touch `.agents/plugins/marketplace.json`, touch `docs/reference/`, or use `/media/u0/Extreme SSD`.
- `H-3` returned a read-only reconciliation brief covering extraction/reconciliation schemas, dedupe-key policy, runner integration seams, and no-publish/no-MCP risks.
- `T-1` added focused WP-06 tests in `tests/test_chatgpt_atlas_guided_reconciliation.py`; the tests initially failed as expected before `L-4` implementation existed.
- `L-4` implemented `mempalace/chatgpt_atlas_guided_reconciliation.py` and atlas-runner integration in `scripts/localai_chatgpt_thread_signals.py`.
- `O-0` ran `.venv/bin/pytest tests/test_chatgpt_atlas_guided_reconciliation.py tests/test_localai_chatgpt_thread_signals.py`: initially `1 failed, 35 passed` because candidate provenance was nested only.
- `L-4` repaired reconciliation provenance to expose candidate identity directly and under nested metadata.
- `O-0` ran `.venv/bin/pytest tests/test_chatgpt_atlas_guided_contract.py tests/test_chatgpt_atlas_guided_bridge.py tests/test_chatgpt_atlas_guided_coverage.py tests/test_chatgpt_atlas_guided_prompt.py tests/test_chatgpt_atlas_guided_reconciliation.py tests/test_localai_chatgpt_thread_signals.py tests/test_chatgpt_atlas_guided_systemd_wrapper.py`: passed, `113 passed`.
- `O-0` ran `bash -n scripts/systemd/start_chatgpt_atlas_guided_extraction_snow_white_iii.sh`: passed.
- `O-0` ran `.venv/bin/ruff check mempalace/chatgpt_atlas_guided_reconciliation.py scripts/localai_chatgpt_thread_signals.py tests/test_chatgpt_atlas_guided_reconciliation.py tests/test_chatgpt_atlas_guided_systemd_wrapper.py`: passed.
- `O-0` ran `.venv/bin/python -m py_compile mempalace/chatgpt_atlas_guided_reconciliation.py scripts/localai_chatgpt_thread_signals.py tests/test_chatgpt_atlas_guided_reconciliation.py tests/test_chatgpt_atlas_guided_systemd_wrapper.py`: passed.
- `O-0` ran `git diff --check -- mempalace/chatgpt_atlas_guided_reconciliation.py scripts/localai_chatgpt_thread_signals.py tests/test_chatgpt_atlas_guided_reconciliation.py scripts/systemd/start_chatgpt_atlas_guided_extraction_snow_white_iii.sh scripts/systemd/README.md tests/test_chatgpt_atlas_guided_systemd_wrapper.py`: passed.
- `V-1F` no-edit verification returned green for WP-06: contract-valid reconciliation rows, deterministic same-candidate dedupe, explicit duplicate rows, distinct-signal preservation, candidate provenance, non-accepted extraction filtering, atlas-runner materialization/counts, legacy preservation, and no destructive/cloud/MCP/old-wing mutation paths.
- `H-4` returned a read-only ops wrapper checklist covering canonical defaults, systemd resource caps, narrow write scope, host/path/LocalAI guards, and wrapper tests.
- `L-5` implemented `scripts/systemd/start_chatgpt_atlas_guided_extraction_snow_white_iii.sh`, `scripts/systemd/README.md`, and `tests/test_chatgpt_atlas_guided_systemd_wrapper.py`.
- `V-1G` no-edit verification returned green for WP-07: `bash -n` passed, static wrapper tests passed, ruff/py_compile/diff check passed, wrapper uses `mempalace` user, `CPUQuota=200%`, `MemoryMax=16G`, `ProtectSystem=strict`, narrow `ReadWritePaths`, canonical root/LocalAI/token/atlas paths, host/Extreme SSD/path/cloud guards, no publish/MCP args, and no delete/restart/SSH behavior.
- Checkpoint F verdict: green.
- Checkpoint G verdict: green.
- Checkpoint H / WP-08 is unlocked after this milestone is committed and pushed.
- `git commit -m "Add atlas-guided reconciliation and runner"` created milestone commit `c68a785`.
- `git push git@github.com:botman058/mempalace.git HEAD:refs/heads/codex/mempalace-http-mcp-closure` pushed `c68a785` to the fork branch.
- Out-of-scope dirty `.agents/plugins/marketplace.json` and untracked `docs/reference/` remained unstaged.

### 2026-05-12 - WP-08 Activation

- `O-0` reread this worksheet before package activation.
- Current gate: Checkpoint H.
- Activated package: WP-08 only.
- Assigned `T-1` as cross-package verification lead using `gpt-5.3-codex-spark` high.
- Assigned `V-1` as no-edit verification support using `gpt-5.3-codex-spark` high.
- WP-09 through WP-14 remain blocked.
- WP-08 write scope is limited to focused cross-package tests/fixtures if a concrete gap is found; otherwise it is no-edit verification evidence only.
- WP-08 must not call LocalAI, cloud APIs, MCP, Chroma services, remote SSH, or mutate palace data; it must not touch `.agents/plugins/marketplace.json`, `docs/reference/`, or `/media/u0/Extreme SSD`.

### 2026-05-12 - WP-08 Repair And Green Verification

- `T-1` completed cross-package verification in no-edit mode and returned green on the scoped suite with 113 passing tests plus ruff, py_compile, bash syntax, and diff checks.
- `V-1H` completed independent no-edit verification and returned amber because direct `scripts/localai_chatgpt_thread_signals.py --atlas-guided` runs still used the permissive legacy LocalAI URL guard; the snow-white-only guard existed only in the wrapper path.
- `O-0` kept WP-09 blocked, entered worksheet/status repair mode, and assigned `L-3R4` to the smallest repair scope: `scripts/localai_chatgpt_thread_signals.py` and `tests/test_localai_chatgpt_thread_signals.py`.
- `L-3R4` added strict direct atlas-guided LocalAI allowlisting for `http://snow-white-iii:8080/v1` and `http://snow-white-iii.local:8080/v1` before provider creation, while preserving legacy thread-signal localhost behavior outside atlas-guided mode.
- `O-0` ran the repaired WP-08 suite: `tests/test_chatgpt_atlas_guided_contract.py`, `tests/test_chatgpt_atlas_guided_bridge.py`, `tests/test_chatgpt_atlas_guided_coverage.py`, `tests/test_chatgpt_atlas_guided_prompt.py`, `tests/test_chatgpt_atlas_guided_reconciliation.py`, `tests/test_localai_chatgpt_thread_signals.py`, and `tests/test_chatgpt_atlas_guided_systemd_wrapper.py`; result: 115 passed.
- `O-0` ran scoped ruff checks, py_compile checks, `bash -n scripts/systemd/start_chatgpt_atlas_guided_extraction_snow_white_iii.sh`, and `git diff --check`; all passed.
- `V-1H2` completed independent no-edit repair verification and returned green with 115 passing tests plus ruff, py_compile, bash syntax, and diff checks.
- Checkpoint H verdict: green.
- Checkpoint H disposition: WP-09 independent safety review is unlocked after this milestone commit/push.

### 2026-05-12 - WP-09 Activation

- `O-0` reread this worksheet before package activation.
- Current gate: Checkpoint I.
- Activated package: WP-09 only.
- Assigned `R-1` as independent safety review lead using `gpt-5.5` high.
- Assigned `V-1` as no-edit verification support using `gpt-5.3-codex-spark` high.
- WP-10 through WP-14 remain blocked.
- WP-09 scope is review-only across atlas-guided modules, scripts, tests, docs, and wrapper surfaces.
- WP-09 must not call LocalAI, cloud APIs, MCP, Chroma services, remote SSH, or mutate palace data; it must not touch `.agents/plugins/marketplace.json`, `docs/reference/`, or `/media/u0/Extreme SSD`.

### 2026-05-12 - WP-09 Review Red And Repair Activation

- `V-1` returned green overall with two amber gaps: direct atlas-guided CLI run dirs can be arbitrary, and the snow-white wrapper has an explicit `MEMPALACE_INSTALL_ALLOW_OTHER_HOST` bypass.
- `R-1` returned red: direct atlas-guided CLI can write outside the canonical guided run root and overwrite existing diagnostic artifacts through explicit `--run-dir` or `LOCALAI_THREAD_SIGNAL_RUN_DIR`.
- `R-1` also confirmed no delete primitives, atlas-guided `--publish` refusal, disabled publish checkpoint, strict snow-white LocalAI URL allowlisting, and prompt parser rejection of control/provider/path/publish keys.
- Checkpoint I verdict: red.
- Checkpoint I disposition: WP-10 remains blocked.
- `O-0` entered scoped repair mode and assigned `L-3R5` using `gpt-5.4` high to repair direct CLI atlas-guided run-dir confinement in `scripts/localai_chatgpt_thread_signals.py` and `tests/test_localai_chatgpt_thread_signals.py`.
- `O-0` assigned `L-5R` using `gpt-5.4` high to remove or hard-disable the live wrapper host-bypass in `scripts/systemd/start_chatgpt_atlas_guided_extraction_snow_white_iii.sh` and `tests/test_chatgpt_atlas_guided_systemd_wrapper.py`.
- `L-3R5` and `L-5R` must not touch docs, changelog, `.agents/plugins/marketplace.json`, `docs/reference/`, `/media/u0/Extreme SSD`, or live/remote services.

### 2026-05-12 - WP-09 Safety Repair Landed

- `L-3R5` repaired the direct atlas-guided CLI run-dir blocker in `scripts/localai_chatgpt_thread_signals.py`: explicit `--run-dir` and `LOCALAI_THREAD_SIGNAL_RUN_DIR` are rejected for atlas-guided CLI use unless they resolve under `DEFAULT_ATLAS_GUIDED_RUN_DIR`, are not the root itself, and do not use `/media/u0/Extreme SSD`.
- `L-3R5` preserved the deterministic implicit atlas-guided child run dir and legacy non-atlas run-dir behavior.
- `L-3R5` added focused tests for safe child acceptance, unsafe explicit run-dir rejection before side effects, unsafe env run-dir rejection, and legacy non-atlas behavior.
- `L-5R` removed the live wrapper `MEMPALACE_INSTALL_ALLOW_OTHER_HOST` bypass and updated static wrapper tests to require the strict snow-white host guard and absence of the bypass variable.
- `O-0` ran the repaired scoped suite: `tests/test_chatgpt_atlas_guided_contract.py`, `tests/test_chatgpt_atlas_guided_bridge.py`, `tests/test_chatgpt_atlas_guided_coverage.py`, `tests/test_chatgpt_atlas_guided_prompt.py`, `tests/test_chatgpt_atlas_guided_reconciliation.py`, `tests/test_localai_chatgpt_thread_signals.py`, and `tests/test_chatgpt_atlas_guided_systemd_wrapper.py`; result: 118 passed.
- `O-0` ran scoped ruff checks, py_compile checks, `bash -n scripts/systemd/start_chatgpt_atlas_guided_extraction_snow_white_iii.sh`, and `git diff --check`; all passed.
- Checkpoint I disposition remains blocked until independent re-review returns green.

### 2026-05-12 - WP-09 / Checkpoint I Green

- `V-1I2` independently re-checked the repaired safety invariants and found no red issues: direct CLI atlas run-dir confinement, root refusal, `/media/u0/Extreme SSD` refusal, deterministic default child preservation, legacy non-atlas preservation, strict snow-white wrapper host policy, no publish/MCP args, service user/resource caps, and narrow write path were all present.
- `V-1I2` reported an environment amber because it did not use the repo `.venv` and hit a missing ambient `chromadb` import before pytest collection; O-0's `.venv` suite evidence already covers the test execution gap.
- `R-1R` returned green with file/line evidence for direct atlas-guided CLI run-dir confinement, `/media/u0/Extreme SSD` refusal, validation before provider creation or artifact writes, test coverage, wrapper host-bypass removal, no default publish, no old-wing mutation, publish gate constraints, strict snow-white LocalAI constraints, and no delete primitive in reviewed surfaces.
- Checkpoint I verdict: green.
- Checkpoint I disposition: WP-10 bounded no-publish remote smoke is unlocked after this milestone commit/push.

### 2026-05-12 - WP-10 Activation

- `O-0` reread this worksheet before package activation.
- Current gate: Checkpoint J.
- Activated package: WP-10 only.
- Assigned `L-5` as live ops lead using `gpt-5.4` high.
- Assigned `V-1` as no-edit smoke verification support using `gpt-5.3-codex-spark` high.
- WP-11 through WP-14 remain blocked.
- WP-10 must use `scripts/systemd/start_chatgpt_atlas_guided_extraction_snow_white_iii.sh` on `snow-white-iii`.
- WP-10 must remain bounded and no-publish, must not call cloud APIs, must not call MCP publish tools, must not delete data, and must not use `/media/u0/Extreme SSD`.
- WP-10 acceptance requires a limited run directory with progress, checkpoints, coverage/candidate copies, extraction, reconciliation, disabled publish checkpoint, service/resource-cap evidence, and no-publish evidence.

### 2026-05-12 - WP-10 Smoke Red And Materialization Repair

- `L-5` staged committed `HEAD` `c2408c5` to `/media/u0/OneDrive_Backup/tmp-mempalace/codex-mempalace-app-20260513T023023Z-c2408c5/app` using `git archive` and excluded `.agents/plugins/marketplace.json`.
- `L-5` promoted the staged app with the live `promote_snow_white_iii_app_update.sh`; promotion reported no file deletion, no service restart, and no palace data touch.
- `L-5` confirmed the live wrapper exists at `/media/u0/OneDrive_Backup/mempalace/app/scripts/systemd/start_chatgpt_atlas_guided_extraction_snow_white_iii.sh` owned by `mempalace:mempalace`.
- `L-5` attempted bounded no-publish smoke with run id `atlas_guided_smoke_20260513T023135Z_l5`, `--limit 2`, and `--provider-max-attempts 1`.
- The wrapper stopped before `systemd-run`; no transient unit, journal entries, guided run directory, or guided smoke artifacts were created.
- Failure reason: canonical atlas run `/media/u0/OneDrive_Backup/mempalace/data/chatgpt_archive_atlas/atlas_full2_20260512T0412Z_2fc8ac5` is complete as a pre-LLM atlas and has `topic_clusters.jsonl` plus `thread_index.jsonl`, but lacks `candidate_bridge_records.jsonl`, `atlas_thread_candidates.jsonl`, and `atlas_candidate_coverage.json`.
- Checkpoint J verdict: red.
- Checkpoint J disposition: WP-11 remains blocked. Repair assigned to `L-2R3` to add a repeatable pure materialization path for the missing guided candidate artifacts, with no LocalAI, no MCP, no cloud calls, no deletion, and no `/media/u0/Extreme SSD`.

### 2026-05-12 - WP-10 Materialization Repair Landed

- `L-2R3` added `scripts/materialize_chatgpt_atlas_guided_inputs.py`, a pure local-file CLI that reads archive-atlas `topic_clusters.jsonl` and `thread_index.jsonl`, builds `candidate_bridge_records.jsonl`, `atlas_thread_candidates.jsonl`, and `atlas_candidate_coverage.json` with the existing WP-02/WP-03 helpers, and prints a JSON summary.
- The materializer confines live atlas dirs to child directories under `/media/u0/OneDrive_Backup/mempalace/data/chatgpt_archive_atlas`, refuses `/media/u0/Extreme SSD`, treats identical existing outputs as already materialized, refuses non-identical existing artifacts, and uses exclusive final-file creation without temp-file cleanup or unlink.
- `L-2R3` added `tests/test_materialize_chatgpt_atlas_guided_inputs.py` and updated `scripts/systemd/README.md` to document the materialization prerequisite before bounded smoke; the stale wrapper host-bypass note was removed.
- `O-0` made an integration repair to avoid temp-file unlink cleanup in the materializer and added a regression test asserting no `tempfile` or `.unlink()` usage.
- `O-0` ran `.venv/bin/pytest tests/test_materialize_chatgpt_atlas_guided_inputs.py tests/test_chatgpt_atlas_guided_bridge.py tests/test_chatgpt_atlas_guided_coverage.py tests/test_chatgpt_atlas_guided_systemd_wrapper.py`: 25 passed.
- `O-0` ran the full atlas-guided suite including the new materializer tests: 124 passed.
- `O-0` ran scoped ruff checks, py_compile checks, `bash -n scripts/systemd/start_chatgpt_atlas_guided_extraction_snow_white_iii.sh`, direct materializer `--help`, and `git diff --check`; all passed.
- Checkpoint J disposition remains blocked until the repaired app is promoted, the canonical atlas guided inputs are materialized, and the bounded no-publish smoke rerun is green.

### 2026-05-12 - WP-10 / Checkpoint J Green

- `L-5R2` staged committed `HEAD` `73285d6cbd6519bc2cf23c67331fbe42a6d4e110` to `/media/u0/OneDrive_Backup/tmp-mempalace/codex-mempalace-app-20260513T024832Z-73285d6/app` using `git archive`; `.agents/plugins/marketplace.json` was excluded.
- `L-5R2` promoted the staged app with the live promotion wrapper. Promotion reported no deletion, no service restart, and no palace data touch.
- `L-5R2` materialized guided inputs on `snow-white-iii` with the live materializer as `mempalace`: `candidate_bridge_records.jsonl` has 3120 rows, `atlas_thread_candidates.jsonl` has 4746 rows, `atlas_candidate_coverage.json` exists, and coverage status is `needs_review`.
- `L-5R2` ran bounded no-publish smoke through the live wrapper with run id `wp10smoke20260513t025130z`, `--limit 2`, and `--provider-max-attempts 1`.
- The transient unit was `mempalace-chatgpt-atlas-guided-wp10smoke20260513t025130z.service`; it completed with `Result=success` and `ExecMainStatus=0` before being collected by `systemd-run --collect`.
- Smoke run directory: `/media/u0/OneDrive_Backup/mempalace/data/atlas_guided_chatgpt_signals/wp10smoke20260513t025130z`.
- `progress.json` reports `status=complete`, `phase_status=complete`, `no_publish=true`, `publish_enabled=false`, `segments_processed_this_run=2`, `accepted_records=16`, `extraction_records=16`, `reconciled_signals=16`, `invalid_outputs=0`, and `provider_error_records=0`.
- Artifact counts in the smoke run: `candidate_bridge_records.jsonl` 3120, `atlas_thread_candidates.jsonl` 4746, `extraction_records.jsonl` 16, `reconciled_signals.jsonl` 16, `publish_checkpoint.jsonl` 1, `segment_checkpoint.jsonl` 2, and `source_checkpoint.jsonl` 1; `invalid_outputs.jsonl` was absent with zero invalid output counts.
- `publish_checkpoint.jsonl` row has `status=disabled`, `publish_enabled=false`, `publish_gate_open=false`, and `record_count=0`.
- Live wrapper evidence remains `--property=User=mempalace`, `--property=Group=mempalace`, `--property=ReadWritePaths="$RUN_DIR"`, `--property=MemoryMax=16G`, `--property=CPUQuota=200%`, `--atlas-guided`, and no `--publish`.
- `V-1J` independently verified the smoke run artifacts, no-publish evidence, row counts, transient unit/journal evidence, and wrapper resource caps; verdict: green.
- Checkpoint J verdict: green.
- Checkpoint J disposition: WP-11 full atlas-guided no-publish extraction is unlocked after this milestone commit/push.

### 2026-05-13 - WP-11 Activation

- `O-0` reread this worksheet before package activation.
- Current gate: Checkpoint K.
- Activated package: WP-11 only.
- Assigned `L-5` as live ops lead using `gpt-5.4` high.
- Assigned `V-1` as no-edit run verification support using `gpt-5.3-codex-spark` high.
- WP-12 through WP-14 remain blocked.
- WP-11 must use `scripts/systemd/start_chatgpt_atlas_guided_extraction_snow_white_iii.sh` on `snow-white-iii`.
- WP-11 must run no-publish, must not call cloud APIs, must not call MCP publish tools, must not delete data, and must not use `/media/u0/Extreme SSD`.
- WP-11 should use the already-materialized guided inputs under `/media/u0/OneDrive_Backup/mempalace/data/chatgpt_archive_atlas/atlas_full2_20260512T0412Z_2fc8ac5`.
- WP-11 acceptance requires a completed or cleanly resumable run directory with progress, checkpoints, extraction, reconciliation, disabled publish checkpoint, service/resource-cap evidence, and no-publish evidence.

### 2026-05-12 - WP-00 / Checkpoint A Green

- `O-0` created this worksheet in worksheet/status mode.
- Current local branch truth before worksheet creation: `codex/mempalace-http-mcp-closure` at `5fad9d9`.
- Current dirty files remain out of scope: modified `.agents/plugins/marketplace.json` and untracked `docs/reference/`.
- `O-0` ran `git diff --check -- docs/worksheets/mempalace_chatgpt_atlas_guided_mining_worksheet_2026-05-12.md`: passed.
- `O-0` checked worksheet heading order against the Tako-required structure.
- Checkpoint A required evidence is present: worksheet exists on disk, branch/head/status are recorded, completed atlas run id is recorded, diagnostic old-run path is recorded, dirty-file scope is recorded, and corrected lead/helper model assignments are recorded.
- Checkpoint A verdict: green.
- Checkpoint A disposition: WP-01 artifact contract work is unlocked.
- `git commit -m "Add atlas-guided mining worksheet"` created `d71df9d` with only this worksheet staged.
- `git push git@github.com:botman058/mempalace.git HEAD:refs/heads/codex/mempalace-http-mcp-closure` pushed `d71df9d` to the fork branch.
- Out-of-scope dirty `.agents/plugins/marketplace.json` and untracked `docs/reference/` remained unstaged.
- `O-0` added explicit checkpoint, package status, drift, and decision ledgers after user correction before committing the second WP-00 evidence update.
