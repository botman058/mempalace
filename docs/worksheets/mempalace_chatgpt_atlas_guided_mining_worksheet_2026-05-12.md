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
| B - Atlas-Guided Contract | active | Not started; contract work is unlocked after Checkpoint A. | WP-02/WP-04 design skeleton after green verdict |
| C - Atlas Bridge | blocked | Waiting on WP-01/WP-02. | WP-03 after green verdict |
| D - Candidate Coverage | blocked | Waiting on WP-03. | WP-04/WP-05 after green verdict |
| E - Prompt/Parser | blocked | Waiting on WP-04. | WP-05 after green verdict |
| F - Extraction And Reconciliation | blocked | Waiting on WP-05/WP-06. | WP-07/WP-08 after green verdict |
| G - Ops Wrapper | blocked | Waiting on WP-07. | WP-09 after Checkpoint H also green |
| H - Cross-Package Verification | blocked | Waiting on WP-08. | WP-09 after green verdict |
| I - Safety Review | blocked | Waiting on WP-09. | WP-10 after green verdict |
| J - Bounded Remote Smoke | blocked | Waiting on WP-10. | WP-11 after green verdict |
| K - Full No-Publish Extraction | blocked | Waiting on WP-11. | WP-12 after green verdict |
| L - Publish Readiness | blocked | Waiting on WP-12. | WP-13 or no-publish closure |
| M - Publish Smoke | blocked | Optional; waiting on WP-13 activation and explicit review recommendation. | WP-14 after green verdict |
| N - Closure | blocked | Waiting on final docs/devlog/tests/run evidence and commit/push. | Tranche closed |

---

## package status ledger

| Package | Status | Owner/lead | Notes |
|---|---|---|---|
| WP-00 | complete | `O-0` | Worksheet and baseline freeze are complete; Checkpoint A is green. |
| WP-01 | unlocked | `L-1` | Artifact contract is the active next package; no implementation package may bypass it. |
| WP-02 | blocked | `L-2` | Requires Checkpoint B green. |
| WP-03 | blocked | `L-2` | Requires Checkpoint C green. |
| WP-04 | blocked | `L-3` | Requires Checkpoint B/C/D sequencing as recorded in package table. |
| WP-05 | blocked | `L-3` | Requires Checkpoint E green. |
| WP-06 | blocked | `L-4` | Requires WP-05 extraction mode. |
| WP-07 | blocked | `L-5` | May only proceed within the recorded ops wrapper scope. |
| WP-08 | blocked | `T-1` | Requires WP-02 through WP-07 evidence. |
| WP-09 | blocked | `R-1` | Independent safety review only after cross-package verification. |
| WP-10 | blocked | `L-5` | Bounded no-publish remote smoke only after safety review. |
| WP-11 | blocked | `L-5` | Full no-publish extraction only after bounded smoke. |
| WP-12 | blocked | `L-4` | Publish-readiness review only after full no-publish artifacts exist. |
| WP-13 | blocked | `L-5` | Optional tiny publish smoke only after explicit green recommendation. |
| WP-14 | blocked | `O-0` | Closure docs/devlog/commit/push after publish smoke or explicit no-publish closure. |

---

## drift ledger

| Date | Status | Drift item | Disposition |
|---|---|---|---|
| 2026-05-12 | closed | Initial WP-00 worksheet draft omitted explicit checkpoint/package/drift/decision ledger sections. | Recovered in worksheet/status mode before the second WP-00 evidence commit; no implementation package was activated and no code was touched. |
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

---

## execution log

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
