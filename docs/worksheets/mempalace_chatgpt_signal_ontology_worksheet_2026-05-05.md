# MemPalace ChatGPT Signal Ontology Recovery - Orchestrated Worksheet
Date: 2026-05-05
Repo baseline: `/home/u4/repos/mempalace`
Live branch baseline: `codex/mempalace-http-mcp-closure` at `4fdc3f4`
Observed branch relation: local checkout on closure branch; only observed dirty file is out-of-scope `.agents/plugins/marketplace.json`
Document type: implementation worksheet
Objective: recover completed `chatgpt_signals` LocalAI classifications into an inspectable, progressive, dashboard-visible semantic `wing:room` ontology without deleting or mutating the original signal drawers.

---

## control plane

### Top-level orchestrator

- **Only top-level orchestrator:** `O-0`
- **Model:** `gpt-5.5`
- **Reasoning depth:** `xhigh`
- **Authority:** assign packages, enforce mutation lock, review evidence, arbitrate taxonomy contract, integrate reviewed patches, update worksheet/devlog, push final branch
- **Forbidden uses:** direct package implementation, unannounced repo edits, deleting palace data, mutating original `chatgpt_signals` drawers, touching `.agents/plugins/marketplace.json`, using `/media/u0/Extreme SSD`, cloud LLM upload without separate explicit approval
- **Mutation lock:** `O-0` is read/review/orchestrate-only by default. Direct implementation edits are forbidden except in declared worksheet/status, integration, or emergency repair mode.

### Working rule

One worksheet controls this tranche: `docs/worksheets/mempalace_chatgpt_signal_ontology_worksheet_2026-05-05.md`.

`O-0` rereads this worksheet before package activation, worker acceptance, checkpoint closure, and devlog/handoff updates.

### Current hard gate

Checkpoint A is the active gate. `WP-00` worksheet creation is the only mutation allowed in this package. After Checkpoint A is green, the next permitted package activation is WP-01. No ontology code, dashboard code, MCP mutation path, service change, or remote apply may start before WP-01 activation.

---

## reasoning-depth matrix

| Model | Reasoning depth | Intended uses | Forbidden uses |
|---|---:|---|---|
| `gpt-5.5` | `xhigh` | `O-0` orchestration, architecture arbitration, checkpoint verdicts, final integration | direct package implementation outside declared mutation modes |
| `gpt-5.4` | high | ontology pipeline lead, MCP/storage safety lead, independent review | unrelated refactors, UI styling ownership |
| `gpt-5.4-mini` | medium | dashboard UI/progress panel, focused tests, docs/systemd helpers | taxonomy architecture ownership |
| `gpt-5.3-codex` | medium | bounded implementation patches with clear file ownership | broad redesign |
| `gpt-5.3-codex-spark` | medium | narrow verification, syntax checks, fixture generation | architecture or safety review |

---

## standing constraints

1. Do not delete files or palace data without explicit confirmation.
2. Do not mutate original `chatgpt_signals` drawers.
3. Do not overwrite outside designated working folders.
4. Canonical remote app and palace paths are under `/media/u0/OneDrive_Backup/mempalace`.
5. Run artifacts must live under `/media/u0/OneDrive_Backup/mempalace/data/ontology/<run_id>/`.
6. Do not use `/media/u0/Extreme SSD`.
7. LocalAI runs on `snow-white-iii`; cloud APIs are not allowed unless a later explicit manual approval is given for a previewed unresolved batch.
8. Dashboard progress must be read-only and must not compete with active ontology, mining, or classification writes.
9. CPU cap target remains 200%; memory cap target remains 16G.
10. Do not stage or modify `.agents/plugins/marketplace.json`.
11. Preserve remote serving model: `snow-white-iii` hosts MemPalace for tailnet clients.
12. Use deterministic IDs for routed semantic copies so reruns are idempotent.

---

## O-0 mutation lock

`O-0` is read/review/orchestrate-only until a package has explicit activation, bounded worker ownership, returned implementation evidence, required independent review, and an `O-0` checkpoint verdict.

`O-0` must not directly edit repo files, call `apply_patch`, run write commands, run rewriting formatters, generate migrations/codegen, stage commits, or push during package implementation.

Allowed mutation modes:

- `worksheet/status mode`: worksheet, drift ledger, status, devlog, and handoff truth only.
- `integration mode`: reviewed worker-patch integration only.
- `emergency repair mode`: recorded bypass only.

Every mutation mode must be announced before the first write:

`Current gate: <mode>; allowed write scope: <paths>; reason: <checkpoint/package>.`

Any unannounced direct `O-0` code edit is red drift and invalidates the package checkpoint until reviewed.

---

## preserved baseline

- Completed LocalAI signal classification exists in the `chatgpt_signals` wing.
- `chatgpt_signals` is source classification output, not a semantic wing.
- Existing first-pass rooms are evidence only; they are not final rooms.
- Rooms are not globally unique. Final candidates are canonical `wing:room` pairs.
- Current branch is `codex/mempalace-http-mcp-closure` at `4fdc3f4`.
- Worktree has out-of-scope dirty `.agents/plugins/marketplace.json`.
- `mempalace-http.service` and `mempalace-dashboard.service` were previously verified active on `snow-white-iii`.
- `mempalace-localai-chatgpt-signals.service` was previously verified inactive/dead with `Result=success`.
- Fork push target remains `git@github.com:botman058/mempalace.git`.

---

## agent pool

| ID | Model | Depth | Role | Intended use | Forbidden use |
|---|---|---:|---|---|---|
| O-0 | `gpt-5.5` | xhigh | Orchestrator/integrator | Assign, review, checkpoint, integrate | package implementation |
| A-1 | `gpt-5.4` | high | Ontology contract lead | artifact schemas, prompt contracts, taxonomy invariants | dashboard UI implementation |
| A-2 | `gpt-5.4` | high | Storage/MCP safety lead | safe export, copy semantics, active-run guards | taxonomy design ownership |
| A-3 | `gpt-5.4` | high | Ontology algorithm lead | clustering, candidate retrieval, iteration design | MCP mutation implementation |
| A-4 | `gpt-5.4-mini` | medium | Dashboard backend worker | read-only ontology progress endpoints | ontology classification logic |
| A-5 | `gpt-5.4-mini` | medium | Dashboard UI worker | progress meter, run browser, artifact inspection UI | backend mutation paths |
| B-1 | `gpt-5.4-mini` | medium | Test worker | fixtures, unit tests, tiny-palace integration | broad refactors |
| B-2 | `gpt-5.3-codex` | medium | CLI/materialization worker | CLI shell, progress writer, resume files | final safety review |
| R-1 | `gpt-5.4` | high | Independent reviewer | no-delete/no-mutate/idempotency/dashboard safety review | implementation under review |

---

## package overview

| Package | Lead | Purpose | Size | Blocked by? |
|---|---|---|---:|---|
| WP-00 | O-0 | Create worksheet and freeze baseline | S | none |
| WP-01 | A-1 | Define run artifact and progress schemas | S | WP-00 |
| WP-02 | A-2 | Add safe source drawer export | S | WP-01 |
| WP-03 | A-2 | Add idempotent semantic copy support | S | WP-02 |
| WP-04 | B-2 | Add ontology CLI shell and run directory lifecycle | S | WP-01 |
| WP-05 | B-2 | Add progressive materialization and resume markers | S | WP-04 |
| WP-06 | A-1 | Add LocalAI prompt/parser for open `wing1:room1` pass | S | WP-05 |
| WP-07 | A-3 | Add candidate clustering from `wing1:room1` artifacts | M | WP-06 |
| WP-08 | A-1 | Add canonical candidate naming/pruning | S | WP-07 |
| WP-09 | A-3 | Add candidate retrieval for per-drawer route choices | S | WP-08 |
| WP-10 | A-1 | Add pass2 route prompt/parser | S | WP-09 |
| WP-11 | A-1 | Add local verification pass | S | WP-10 |
| WP-12 | A-3 | Add iteration controller and convergence reports | M | WP-11 |
| WP-13 | A-4 | Add dashboard read-only progress endpoints | S | WP-05 |
| WP-14 | A-5 | Add dashboard progress meter and artifact browser | S | WP-13 |
| WP-15 | B-1 | Add contract/unit tests | M | WP-01-WP-14 |
| WP-16 | B-1 | Add tiny-palace integration tests | S | WP-03, WP-12 |
| WP-17 | R-1 | Independent safety and drift review | S | WP-15, WP-16 |
| WP-18 | O-0 | Integration, docs/devlog, verification, commit, push | S | WP-17 |

---

## orchestration protocol

Workers own bounded packages. `O-0` assigns, reviews, accepts or rejects, records drift, and integrates only after evidence.

### Implementation ownership rule

Workers implement bounded packages. `O-0` assigns, reviews, accepts/rejects, records drift, and integrates only after evidence. `O-0` must not preempt worker implementation because a change appears obvious.

### Submilestone loop

1. `O-0` rereads this worksheet.
2. `O-0` activates exactly one package or a non-conflicting parallel package set.
3. Worker implements bounded slice in assigned files only.
4. Worker returns evidence: changed paths, behavior summary, tests/checks, known gaps.
5. `O-0` reviews evidence against checkpoint requirements.
6. Independent review runs where required.
7. `O-0` records green/amber/red checkpoint verdict.
8. Only after green verdict may downstream package start.

### Progress/materialization rule

Long ontology work must materialize progressively.

Every long phase must write:

- `progress.json`: current phase, counts, elapsed time, last update, status.
- `<phase>.jsonl`: one durable line per processed drawer or candidate.
- `artifacts_index.json`: stable list of produced files and schema names.
- `unresolved.jsonl`: append-only unresolved/conflict records as soon as they are known.

Dashboard progress is part of V1. The dashboard must inspect these artifacts during a run without waiting for completion.

### Evidence rules

Acceptable evidence:

- targeted tests for no mutation of `chatgpt_signals`
- idempotency tests for semantic copies
- progress artifact tests for incremental writes
- dashboard tests showing live progress reads without starting heavy backend work
- dry-run evidence proving no palace writes
- apply evidence against a tiny palace only
- independent review confirming no deletes and no automatic cloud upload path

Insufficient evidence:

- worker summary alone
- docs saying progress exists
- CLI progress without persisted artifacts
- dashboard mockup without reading real run artifact shapes
- tests that pass only with completed runs
- any route acceptance that bypasses local verification
- any in-place metadata update to original `chatgpt_signals`

---

## checkpoints and gates

### Checkpoint A - Worksheet Baseline Green

- **Proves:** tranche is controlled by a saved mutation-lock worksheet.
- **Required evidence:** worksheet exists on disk; branch/head/status recorded; `.agents/plugins/marketplace.json` noted out of scope; O-0 model/depth recorded as `gpt-5.5/xhigh`.
- **Insufficient evidence:** worksheet draft in chat only.
- **Disposition:** green unlocks WP-01.

### Checkpoint B - Artifact Contract Green

- **Proves:** ontology runs are inspectable and resumable before implementation details sprawl.
- **Required evidence:** schemas for progress, phase JSONL, artifact index, accepted routes, unresolved routes, and routed copy metadata.
- **Insufficient evidence:** only CLI print output.
- **Disposition:** green unlocks WP-02 through WP-05 and WP-13 contract work.

### Checkpoint C - Source Export Green

- **Proves:** implementation can read source signal drawers without mutating originals.
- **Required evidence:** tests for paginated export, full content preservation, metadata preservation, and read-only behavior.
- **Insufficient evidence:** manual dashboard browsing or search results.
- **Disposition:** green unlocks WP-03.

### Checkpoint D - Semantic Copy Green

- **Proves:** routed copies can be created idempotently without touching originals.
- **Required evidence:** deterministic ID tests, origin metadata tests, repeated-copy no-op tests, active-run apply refusal tests.
- **Insufficient evidence:** one successful manual copy.
- **Disposition:** green unlocks apply-capable later packages.

### Checkpoint E - Progressive Run Green

- **Proves:** long-running ontology work can be inspected during execution.
- **Required evidence:** dry-run writes run directory, `progress.json`, `artifacts_index.json`, phase JSONL, and resume markers incrementally.
- **Insufficient evidence:** final report only.
- **Disposition:** green unlocks LocalAI passes and dashboard progress integration.

### Checkpoint F - Pass1 Candidate Green

- **Proves:** first ontology pass creates usable open-ended `wing1:room1` proposals.
- **Required evidence:** mocked LocalAI tests, parser tests, invalid JSON handling, sample `pass1_open.jsonl`.
- **Insufficient evidence:** one successful LocalAI call.
- **Disposition:** green unlocks clustering.

### Checkpoint G - Canonical Candidate Green

- **Proves:** open proposals become canonical candidate `wing:room` pairs without assuming rooms are globally unique.
- **Required evidence:** clustering tests, naming/pruning tests, sample candidate artifact, examples retained per candidate.
- **Insufficient evidence:** flat room list or wing-only taxonomy.
- **Disposition:** green unlocks route candidate retrieval.

### Checkpoint H - Routing Green

- **Proves:** each drawer can be routed against candidate canonical `wing:room` pairs plus `null`.
- **Required evidence:** candidate retrieval tests, route parser tests, null/low-confidence/invalid JSON tests.
- **Insufficient evidence:** confidence score without candidate provenance.
- **Disposition:** green unlocks local verification.

### Checkpoint I - Verification And Iteration Green

- **Proves:** accepted routes pass local verification and unresolved/conflicting cases materialize for review.
- **Required evidence:** accepted, null, low-confidence, conflict, and repeated-iteration tests; convergence report sample.
- **Insufficient evidence:** single pass output only.
- **Disposition:** green unlocks dashboard and integration tests.

### Checkpoint J - Dashboard Progress Green

- **Proves:** dashboard exposes live ontology progress and artifacts read-only.
- **Required evidence:** dashboard tests for active run, completed run, failed/interrupted run, artifact list, unresolved preview, and progress meter display.
- **Insufficient evidence:** static page rendering without artifact data.
- **Disposition:** green unlocks final review.

### Checkpoint K - Release Green

- **Proves:** tranche is safe to commit and push.
- **Required evidence:** targeted tests pass or documented environment blockers; independent review complete; docs/devlog updated; out-of-scope dirty file unstaged; commit pushed to fork target.
- **Insufficient evidence:** unreviewed worker patch or incomplete worksheet status.
- **Disposition:** tranche closed.

---

## detailed work packages

### WP-00 - Worksheet and Baseline Freeze

- **owner:** `O-0`
- **lead:** `O-0`
- **support:** none
- **objective:** save this worksheet and freeze repo/worktree truth.
- **why:** prevents O-0 drift and uncontrolled ontology mutations.
- **files/subsystems:** `docs/worksheets/mempalace_chatgpt_signal_ontology_worksheet_2026-05-05.md`
- **deliverables:** saved worksheet with truthful branch/head/status and explicit O-0 `gpt-5.5/xhigh`.
- **acceptance:** Checkpoint A green.
- **exit:** WP-01 activation.

### WP-01 - Artifact And Progress Schema Contract

- **owner:** `O-0`
- **lead:** `A-1`
- **support:** `B-2`, `A-4`
- **objective:** define durable run artifact schemas and dashboard-readable progress semantics.
- **why:** progress and resumability must be designed before long-running classification code.
- **files/subsystems:** ontology docs/contracts and schema fixtures.
- **deliverables:** schemas for progress, artifact index, phase records, accepted routes, unresolved routes, and semantic copy metadata.
- **acceptance:** Checkpoint B green.
- **exit:** WP-02, WP-04, and WP-13 may start.

### WP-02 - Safe Source Drawer Export

- **owner:** `O-0`
- **lead:** `A-2`
- **support:** `B-1`
- **objective:** provide paginated full-content export for source `chatgpt_signals` drawers.
- **why:** ontology recovery needs full signal content while preserving original drawers.
- **files/subsystems:** MCP/server storage helpers or equivalent internal export layer.
- **deliverables:** read-only export path with source metadata.
- **acceptance:** Checkpoint C green.
- **exit:** WP-03 activation.

### WP-03 - Idempotent Semantic Copy Support

- **owner:** `O-0`
- **lead:** `A-2`
- **support:** `B-1`
- **objective:** create deterministic routed copies preserving origin metadata.
- **why:** final semantic materialization must be rerunnable and non-destructive.
- **files/subsystems:** MCP/server storage helpers or equivalent internal copy layer.
- **deliverables:** copy operation with deterministic IDs and no-op rerun behavior.
- **acceptance:** Checkpoint D green.
- **exit:** apply-capable later packages may depend on it.

### WP-04 - Ontology CLI Shell And Run Lifecycle

- **owner:** `O-0`
- **lead:** `B-2`
- **support:** `A-1`
- **objective:** add `mempalace ontology chatgpt-signals` with dry-run default and run directory lifecycle.
- **why:** the operator needs a single controlled entry point before classification logic lands.
- **files/subsystems:** CLI and ontology run module.
- **deliverables:** command parser, run ID generation, run directory creation, dry-run behavior.
- **acceptance:** command initializes a run without palace writes.
- **exit:** WP-05 activation.

### WP-05 - Progressive Materialization And Resume Markers

- **owner:** `O-0`
- **lead:** `B-2`
- **support:** `A-4`
- **objective:** write progress and phase artifacts incrementally during all long phases.
- **why:** the dashboard must inspect active runs and interrupted runs.
- **files/subsystems:** progress writer, artifact index writer, resume marker logic.
- **deliverables:** `progress.json`, `artifacts_index.json`, phase JSONL appenders, resume markers.
- **acceptance:** Checkpoint E green.
- **exit:** WP-06 and WP-13 activation.

### WP-06 - Pass1 LocalAI Prompt And Parser

- **owner:** `O-0`
- **lead:** `A-1`
- **support:** `B-1`
- **objective:** classify each drawer into open-ended `wing1:room1` proposal records.
- **why:** completed first pass has no useful semantic wing variation.
- **files/subsystems:** LocalAI prompt, JSON parser, validation helpers.
- **deliverables:** validated `pass1_open.jsonl` records.
- **acceptance:** Checkpoint F green.
- **exit:** WP-07 activation.

### WP-07 - Candidate Clustering

- **owner:** `O-0`
- **lead:** `A-3`
- **support:** `A-1`
- **objective:** cluster `wing1:room1` proposals into candidate canonical `wing:room` groups.
- **why:** ontology candidates must be generated from first-pass proposals without flattening room names globally.
- **files/subsystems:** clustering and candidate grouping module.
- **deliverables:** candidate cluster artifact with examples and centroids.
- **acceptance:** clustering tests preserve room ambiguity across wings.
- **exit:** WP-08 activation.

### WP-08 - Candidate Naming And Pruning

- **owner:** `O-0`
- **lead:** `A-1`
- **support:** `A-3`
- **objective:** name, describe, merge, or prune candidate canonical `wing:room` pairs.
- **why:** route pass needs compact, human-readable candidates.
- **files/subsystems:** LocalAI candidate naming prompt, candidate schema validation.
- **deliverables:** canonical candidate artifact with definitions and examples.
- **acceptance:** Checkpoint G green.
- **exit:** WP-09 activation.

### WP-09 - Route Candidate Retrieval

- **owner:** `O-0`
- **lead:** `A-3`
- **support:** `B-1`
- **objective:** retrieve up to 5 candidate canonical `wing:room` pairs per drawer.
- **why:** pass2 must choose from plausible candidates instead of the entire ontology.
- **files/subsystems:** candidate retrieval over definitions/examples and drawer text.
- **deliverables:** candidate shortlist records per drawer.
- **acceptance:** retrieval tests include lexical and embedding-like fixture cases.
- **exit:** WP-10 activation.

### WP-10 - Pass2 Route Prompt And Parser

- **owner:** `O-0`
- **lead:** `A-1`
- **support:** `B-1`
- **objective:** route each drawer to one candidate canonical `wing:room` or `null`.
- **why:** pass1 candidates are hypotheses; pass2 performs drawer-level reconciliation.
- **files/subsystems:** LocalAI route prompt, parser, validation helpers.
- **deliverables:** route records with selected candidate, confidence, rationale, and null support.
- **acceptance:** Checkpoint H green.
- **exit:** WP-11 activation.

### WP-11 - Local Verification Pass

- **owner:** `O-0`
- **lead:** `A-1`
- **support:** `A-3`
- **objective:** verify proposed routes locally against drawer text, origin room, candidate definition, and rationale.
- **why:** no route should be accepted only because one classifier said so.
- **files/subsystems:** LocalAI verifier prompt, verification parser.
- **deliverables:** accepted, rejected, conflict, and unresolved records.
- **acceptance:** verifier tests cover agreement, disagreement, low confidence, and null.
- **exit:** WP-12 activation.

### WP-12 - Iteration Controller And Convergence Reports

- **owner:** `O-0`
- **lead:** `A-3`
- **support:** `A-1`
- **objective:** iterate unresolved/conflicting cases through split/merge/reroute cycles.
- **why:** ontology convergence needs repeated reconciliation, not a single pass.
- **files/subsystems:** iteration controller and report generator.
- **deliverables:** iteration summaries, convergence report, apply-ready manifest.
- **acceptance:** Checkpoint I green.
- **exit:** WP-16 and WP-17 activation.

### WP-13 - Dashboard Progress Endpoints

- **owner:** `O-0`
- **lead:** `A-4`
- **support:** `B-1`
- **objective:** expose ontology run progress and artifacts through read-only dashboard API endpoints.
- **why:** operator inspection must work during a run without touching Chroma or LocalAI.
- **files/subsystems:** dashboard backend read-only artifact endpoints.
- **deliverables:** run list, run detail, progress, artifact list, unresolved preview endpoints.
- **acceptance:** endpoint tests read artifact fixtures only.
- **exit:** WP-14 activation.

### WP-14 - Dashboard Progress Meter And Artifact Browser

- **owner:** `O-0`
- **lead:** `A-5`
- **support:** `A-4`
- **objective:** add dashboard UI for ontology progress and materialized artifacts.
- **why:** progress must be visible in the dashboard, not only in terminal output.
- **files/subsystems:** dashboard static UI.
- **deliverables:** current phase meter, processed/total, accepted/unresolved/conflict counts, elapsed/ETA, artifact browser, unresolved preview.
- **acceptance:** Checkpoint J green.
- **exit:** WP-15 activation.

### WP-15 - Contract And Unit Tests

- **owner:** `O-0`
- **lead:** `B-1`
- **support:** all package leads
- **objective:** cover schema, parsing, progress, routing, verification, idempotency, and dashboard fixtures.
- **why:** safety must be enforced by tests rather than procedure alone.
- **files/subsystems:** focused tests and fixtures.
- **deliverables:** unit tests for Checkpoints B-J.
- **acceptance:** targeted test suite passes or blockers are documented.
- **exit:** WP-16 activation.

### WP-16 - Tiny-Palace Integration Tests

- **owner:** `O-0`
- **lead:** `B-1`
- **support:** `A-2`, `A-3`
- **objective:** verify behavior against a tiny Chroma palace with fake `chatgpt_signals` drawers.
- **why:** source preservation and routed-copy behavior need end-to-end proof.
- **files/subsystems:** tiny-palace integration tests.
- **deliverables:** dry-run no-write test, apply copy test, rerun idempotency test, original preservation test.
- **acceptance:** integration evidence satisfies storage and apply safety requirements.
- **exit:** WP-17 activation.

### WP-17 - Independent Review

- **owner:** `O-0`
- **lead:** `R-1`
- **support:** none
- **objective:** independently review safety, mutation boundaries, progress visibility, cloud gating, and idempotency.
- **why:** mistakes can duplicate private data, hide progress, or mutate source classification.
- **files/subsystems:** accepted diff and worksheet.
- **deliverables:** review verdict with findings or explicit no-issue statement.
- **acceptance:** all high/medium findings resolved or explicitly deferred.
- **exit:** O-0 may enter integration mode.

### WP-18 - Integration, Docs, Commit, Push

- **owner:** `O-0`
- **lead:** `O-0`
- **support:** none
- **objective:** integrate reviewed patches, update docs/devlog, verify, commit, and push.
- **why:** final branch truth must match implemented behavior.
- **files/subsystems:** accepted worker changes, worksheet, docs, changelog/devlog.
- **deliverables:** final verification log, commit, push to `git@github.com:botman058/mempalace.git`.
- **acceptance:** Checkpoint K green.
- **exit:** tranche closed.

---

## assumptions

- Recovery starts from completed `chatgpt_signals` drawers.
- Original `chatgpt_signals` drawers are immutable source evidence.
- First ontology pass produces open-ended `wing1:room1` proposals.
- Canonical candidates are always `wing:room` pairs; rooms are not globally unique.
- Second pass routes each drawer against candidate canonical `wing:room` pairs plus `null`.
- Iteration default maximum is 3 full route/verify iterations unless explicitly changed.
- Semantic copies land directly in final semantic wings only after local verification.
- Dashboard progress is part of V1, not a later enhancement.
- Progress must materialize progressively to disk for inspection during a run.
- Cloud LLM review is candidate-only, manual-approval-only, and never authoritative.
- LocalAI on `snow-white-iii` is the final verifier.

---

## checkpoint ledger

| Checkpoint | Status | Evidence | Next gate |
|---|---|---|---|
| A - Worksheet Baseline Green | green | Worksheet saved to disk; branch/head/status recorded; O-0 model/depth recorded; milestone commit `e7e1d39` pushed. | WP-01 |
| B - Artifact Contract Green | green | `docs/chatgpt_signal_ontology_artifacts.md` defines required artifact/progress schemas and dashboard read contract; milestone commit `1d02f97` pushed. | WP-02/WP-04/WP-13 |
| C - Source Export Green | green | `mempalace_export_drawers` added with full content, safe metadata, pagination, and read-only tests; milestone commit `8be20f1` pushed. | WP-03 |
| D - Semantic Copy Green | green | `mempalace_copy_drawer` adds deterministic routed copies, origin metadata, no-op reruns, slug validation, and existing palace-lock refusal tests; milestone commit `5c611f3` pushed. | apply-capable later packages |
| E - Progressive Run Green | green | WP-05 materializes initial progress artifacts and resume markers with source-wing consistency checks; milestone commit `6a56036` pushed. | WP-06/WP-13 |
| F - Pass1 Candidate Green | green | WP-06 adds LocalAI/openai-compatible pass1 prompt/parser, invalid-output records, and sample JSONL serialization tests; milestone commit `76d6014` pushed. | WP-07 |
| G - Canonical Candidate Green | green | WP-07 candidate clustering plus WP-08 canonical naming/pruning accepted; candidate `wing:room` ambiguity preserved. | WP-09 |
| H - Routing Green | in progress | WP-09 route candidate retrieval accepted; WP-10 route prompt/parser remains. | WP-10 |
| I - Verification And Iteration Green | blocked | Requires WP-11 and WP-12. | WP-11/WP-12 |
| J - Dashboard Progress Green | green | WP-13 backend endpoints plus WP-14 static dashboard progress UI and contract tests accepted. | WP-15 after routing/verification packages |
| K - Release Green | blocked | Requires WP-17 and WP-18. | WP-17/WP-18 |

---

## package status ledger

| Package | Status | Owner | Notes |
|---|---|---|---|
| WP-00 | complete | O-0 | Worksheet saved and baseline frozen. |
| WP-01 | complete | A-1R | Artifact/progress schema contract accepted at Checkpoint B. |
| WP-02 | complete | A-2R | Safe source drawer export accepted at Checkpoint C; milestone commit `8be20f1` pushed. |
| WP-03 | complete | A-2/Poincare | Idempotent semantic copy support accepted at Checkpoint D; milestone commit `5c611f3` pushed. |
| WP-04 | complete | B-2 | CLI shell and run directory lifecycle accepted; milestone commit `0b76d77` pushed. |
| WP-05 | complete | B-2 | Progressive materialization and resume markers accepted at Checkpoint E; milestone commit `6a56036` pushed. |
| WP-06 | complete | A-1/Faraday | Pass1 LocalAI prompt/parser accepted at Checkpoint F; milestone commit `76d6014` pushed. |
| WP-07 | complete | A-3/Bernoulli | Candidate clustering accepted; milestone commit `780297a` pushed. |
| WP-08 | complete | A-1/Archimedes | Candidate naming/pruning accepted; milestone commit `e6c2906` pushed. |
| WP-09 | complete | A-3R/Kepler | Route candidate retrieval accepted; milestone commit `701ba4a` pushed. |
| WP-10 | pending | A-1 | Pass2 route prompt/parser; unblocked by WP-09. |
| WP-11 | blocked | A-1 | Local verification pass. |
| WP-12 | blocked | A-3 | Iteration controller and convergence reports. |
| WP-13 | complete | A-4/Rawls | Dashboard progress endpoints accepted; milestone commit `fdbf41d` pushed. |
| WP-14 | complete | A-5/James | Dashboard progress meter and artifact browser accepted; milestone commit `d002072` pushed. |
| WP-15 | blocked | B-1 | Contract and unit tests. |
| WP-16 | blocked | B-1 | Tiny-palace integration tests. |
| WP-17 | blocked | R-1 | Independent review. |
| WP-18 | blocked | O-0 | Integration, docs, commit, push. |

---

## drift ledger

### Open drift items

- Unaccepted untracked `docs/reference/` output exists. It is outside the accepted WP-01 package and must not be staged. Deletion requires explicit user confirmation.

### Drift recording rule

Any deviation from this worksheet must be recorded here before the next package closes.

Each drift entry must include:

- date/time
- package
- changed paths
- violated or bypassed gate
- reason
- recovery action
- current verdict: green, amber, or red

### Red drift conditions

- O-0 directly edits implementation files outside a declared mutation mode.
- Any source `chatgpt_signals` drawer is mutated in place.
- Any delete or cleanup touches palace data without explicit confirmation.
- Any cloud LLM upload happens without separate explicit approval.
- Dashboard progress reads trigger Chroma writes, LocalAI calls, mining, classification, or ontology mutation.
- Progress exists only in terminal output and is not materialized to run artifacts.

### 2026-05-05 - WP-01 Scope Drift

- **package:** WP-01
- **changed paths:** `docs/reference/mempalace_chatgpt_signal_ontology_artifact_contract_2026-05-05.md`
- **violated or bypassed gate:** replacement A-1R write scope allowed exactly one new contract document, but an additional untracked `docs/reference/` file is present.
- **reason:** likely leftover worker output; not needed for Checkpoint B.
- **recovery action:** do not stage or accept `docs/reference/`; leave it on disk pending explicit user confirmation before any cleanup.
- **current verdict:** amber; does not block WP-01 acceptance because accepted package excludes the extra file.

---

## decision ledger

### 2026-05-05 - Ontology shape

- Decision: final ontology candidates are canonical `wing:room` pairs.
- Reason: room names are not globally unique.
- Consequence: clustering, routing, verification, and copy IDs must preserve wing context.

### 2026-05-05 - Source immutability

- Decision: `chatgpt_signals` remains immutable source evidence.
- Reason: completed first LocalAI pass is useful evidence and should not be destroyed.
- Consequence: semantic materialization creates copied drawers only.

### 2026-05-05 - Progress visibility

- Decision: progress must be visible in the dashboard and materialized progressively to disk.
- Reason: long ontology runs need inspection during execution, not only after completion.
- Consequence: CLI progress alone is insufficient evidence.

### 2026-05-05 - Cloud policy

- Decision: cloud LLM can only be candidate-generation for unresolved batches after separate approval.
- Reason: local privacy and LocalAI-first policy remain controlling.
- Consequence: every cloud suggestion must pass local verification before apply.

---

## evidence log

### 2026-05-05 - WP-00 Baseline Evidence

- `git branch --show-current` reported `codex/mempalace-http-mcp-closure`.
- `git rev-parse --short HEAD` reported `4fdc3f4`.
- `git status --short --branch` showed branch `codex/mempalace-http-mcp-closure` with only out-of-scope dirty `.agents/plugins/marketplace.json`.
- `git remote -v` showed local `origin` as upstream `git@github.com:MemPalace/mempalace.git`; fork push target remains explicitly `git@github.com:botman058/mempalace.git`.
- Existing worksheets were checked and confirmed to maintain post-assumptions evidence logs.
- Worksheet saved at `docs/worksheets/mempalace_chatgpt_signal_ontology_worksheet_2026-05-05.md`.
- No ontology code, dashboard code, MCP mutation path, service change, remote apply, deletion, or palace mutation was performed.

### 2026-05-05 - WP-00 Milestone Commit Evidence

- `git add docs/worksheets/mempalace_chatgpt_signal_ontology_worksheet_2026-05-05.md` staged only the worksheet.
- `git diff --cached --check` passed.
- `git commit -m "Add ChatGPT signal ontology worksheet"` created `e7e1d39`.
- `git push git@github.com:botman058/mempalace.git HEAD:refs/heads/codex/mempalace-http-mcp-closure` pushed `e7e1d39` to the fork branch.
- Post-push `git status --short --branch` showed only out-of-scope dirty `.agents/plugins/marketplace.json`.

### 2026-05-05 - WP-01 Activation

- `O-0` reread this worksheet before activation.
- WP-01 was assigned to A-1 with model `gpt-5.4` and reasoning depth `high`.
- A-1 write scope is limited to artifact/progress contract documentation and optional schema fixtures; A-1 is forbidden from editing this worksheet, runtime code, dashboard code, MCP code, CLI code, `CHANGELOG.md`, `pyproject.toml`, or `.agents/plugins/marketplace.json`.

### 2026-05-05 - WP-01 Reassignment

- Original A-1 exceeded the small-package window and did not return after a bounded status request.
- `O-0` closed original A-1 without accepting any package output.
- Replacement A-1R was assigned WP-01 with model `gpt-5.4`, reasoning depth `high`, and write scope limited to one new contract document under `docs/`.

### 2026-05-05 - WP-01 Acceptance Evidence

- A-1R delivered `docs/chatgpt_signal_ontology_artifacts.md`.
- The contract defines six required surfaces for Checkpoint B: `progress.json`, phase `<phase>.jsonl`, `artifacts_index.json`, `accepted_routes.jsonl`, `unresolved.jsonl`, and routed copy metadata.
- The contract defines status enums, append-only JSONL semantics, atomic rewrite semantics for JSON summaries, dashboard read rules, privacy constraints, and idempotent routed-copy metadata expectations.
- `O-0` verified `rg` hits for required schema surfaces and `git diff --check` passed for the accepted contract and worksheet.
- `docs/reference/` remains unaccepted and unstaged per the WP-01 drift entry.

### 2026-05-05 - WP-01 Milestone Commit Evidence

- `git add CHANGELOG.md docs/chatgpt_signal_ontology_artifacts.md docs/worksheets/mempalace_chatgpt_signal_ontology_worksheet_2026-05-05.md` staged only accepted WP-01 files.
- Initial staged whitespace check found an extra blank line at EOF in `docs/chatgpt_signal_ontology_artifacts.md`; `O-0` fixed only that accepted document.
- `git diff --cached --check` then passed.
- `git commit -m "Define ChatGPT signal ontology artifacts"` created `1d02f97`.
- `git push git@github.com:botman058/mempalace.git HEAD:refs/heads/codex/mempalace-http-mcp-closure` pushed `1d02f97` to the fork branch.
- The unaccepted `docs/reference/` output and out-of-scope `.agents/plugins/marketplace.json` were not staged.

### 2026-05-05 - WP-01 Milestone Evidence Commit

- `git commit -m "Record ChatGPT ontology WP-01 milestone"` created `7c43e26`.
- `git push git@github.com:botman058/mempalace.git HEAD:refs/heads/codex/mempalace-http-mcp-closure` pushed `7c43e26` to the fork branch.
- Post-push `git status --short --branch` showed only out-of-scope dirty `.agents/plugins/marketplace.json` and unaccepted untracked `docs/reference/`.

### 2026-05-05 - WP-02 and WP-04 Activation

- `O-0` reread this worksheet before activation.
- Current branch head before activation was `7c43e26`.
- WP-02 was assigned to A-2 with model `gpt-5.4` and reasoning depth `high`.
- A-2 write scope is limited to `mempalace/mcp_server.py`, `tests/test_mcp_server.py`, and `website/reference/mcp-tools.md` if needed.
- WP-04 was assigned to B-2 with model `gpt-5.3-codex` and reasoning depth `medium`.
- B-2 write scope is limited to `mempalace/cli.py`, a small new ontology run module under `mempalace/` if needed, and focused CLI tests.
- Both workers were instructed not to touch `.agents/plugins/marketplace.json`, `docs/reference/`, or unrelated package surfaces.

### 2026-05-05 - WP-02 Reassignment

- Original A-2 left scoped edits in `mempalace/mcp_server.py`, `tests/test_mcp_server.py`, and `website/reference/mcp-tools.md` but did not return final package evidence after a bounded status request.
- `O-0` closed original A-2 without accepting WP-02.
- Replacement A-2R was assigned to inspect, finish, and report on the existing scoped WP-02 patch.

### 2026-05-05 - WP-02 Acceptance Evidence

- A-2R finalized scoped edits in `mempalace/mcp_server.py`, `tests/test_mcp_server.py`, and `website/reference/mcp-tools.md`.
- `mempalace_export_drawers` is registered as a read-only MCP tool with optional wing/room filters, full drawer content, safe metadata, and clamped pagination.
- Export metadata reduces `source_file` to basename while preserving downstream provenance fields such as `chunk_index`, `added_by`, `conversation_id`, and `source_drawer_id`.
- `mempalace_get_drawer` now uses the shared metadata sanitizer.
- Export tests cover absent-palace no-create behavior, full content preservation, metadata preservation/sanitization, pagination clamping, and no `add`/`update`/`delete` calls.
- `.venv/bin/python -m pytest -q tests/test_mcp_server.py -k "export_drawers or get_drawer_does_not_leak_absolute_source_file_path or tools_list"` passed: `5 passed, 72 deselected`.
- `.venv/bin/python -m py_compile mempalace/mcp_server.py tests/test_mcp_server.py` passed.
- `git diff --check -- mempalace/mcp_server.py tests/test_mcp_server.py website/reference/mcp-tools.md docs/worksheets/mempalace_chatgpt_signal_ontology_worksheet_2026-05-05.md` passed.

### 2026-05-05 - WP-02 Milestone Commit Evidence

- `git add mempalace/mcp_server.py tests/test_mcp_server.py website/reference/mcp-tools.md docs/worksheets/mempalace_chatgpt_signal_ontology_worksheet_2026-05-05.md` staged only accepted WP-02 files plus worksheet status.
- `git diff --cached --check` passed.
- `git commit -m "Add read-only drawer export tool"` created `8be20f1`.
- `git push git@github.com:botman058/mempalace.git HEAD:refs/heads/codex/mempalace-http-mcp-closure` pushed `8be20f1` to the fork branch.
- Unaccepted `docs/reference/` and out-of-scope `.agents/plugins/marketplace.json` were not staged.

### 2026-05-05 - WP-03 and WP-05 Activation

- `O-0` reread this worksheet before activation.
- Current branch head before activation was `8be20f1`.
- WP-03 was assigned to A-2 with model `gpt-5.4` and reasoning depth `high`.
- A-2 write scope is limited to `mempalace/mcp_server.py`, `tests/test_mcp_server.py`, and `website/reference/mcp-tools.md` if needed.
- WP-05 was assigned to B-2 with model `gpt-5.3-codex` and reasoning depth `medium`.
- B-2 write scope is limited to `mempalace/ontology_run.py`, ontology run tests, and `mempalace/cli.py` only if needed.
- Both workers were instructed not to touch `.agents/plugins/marketplace.json`, `docs/reference/`, or unrelated package surfaces.

### 2026-05-05 - WP-05 Acceptance Evidence

- B-2 extended `mempalace/ontology_run.py`, `mempalace/cli.py`, and `tests/test_ontology_cli.py`.
- Non-dry-run initialization now materializes `run_metadata.json`, `progress.json`, `artifacts_index.json`, append-ready phase JSONL files, `accepted_routes.jsonl`, `unresolved.jsonl`, and `resume_markers.jsonl`.
- JSON summary files use temporary-file replacement writes; JSONL files are append-ready.
- Re-running an existing run appends a `resumed` marker instead of failing.
- `O-0` found and sent back a source-wing consistency bug: resuming the same run ID with a different `--source-wing` could append a conflicting resume marker.
- B-2 repaired the bug by validating existing `run_metadata.json` and `progress.json` source wing before appending a resume marker.
- `.venv/bin/python -m pytest -q tests/test_ontology_cli.py` passed: `10 passed`.
- `.venv/bin/python -m py_compile mempalace/ontology_run.py mempalace/cli.py tests/test_ontology_cli.py` passed.
- Manual smoke verified initialized/resumed marker behavior, progress/index creation, and source-wing mismatch refusal without appending a second marker.
- `git diff --check -- mempalace/ontology_run.py mempalace/cli.py tests/test_ontology_cli.py docs/worksheets/mempalace_chatgpt_signal_ontology_worksheet_2026-05-05.md` passed.

### 2026-05-05 - WP-05 Milestone Commit Evidence

- `git add mempalace/ontology_run.py mempalace/cli.py tests/test_ontology_cli.py docs/worksheets/mempalace_chatgpt_signal_ontology_worksheet_2026-05-05.md` staged only accepted WP-05 files plus worksheet status.
- `git diff --cached --check` passed.
- `git commit -m "Materialize ontology run progress artifacts"` created `6a56036`.
- `git push git@github.com:botman058/mempalace.git HEAD:refs/heads/codex/mempalace-http-mcp-closure` pushed `6a56036` to the fork branch.
- Active WP-03 files, unaccepted `docs/reference/`, and out-of-scope `.agents/plugins/marketplace.json` were not staged.

### 2026-05-05 - WP-03 Review Repair Request

- A-2/Poincare returned a scoped WP-03 patch adding `mempalace_copy_drawer`.
- `O-0` reviewed the patch against the WP-01 artifact contract and found one blocking issue before Checkpoint D acceptance: `canonical_wing` and `canonical_room` used the broad `sanitize_name()` validator instead of enforcing lowercase slug-safe ontology keys matching `^[a-z0-9_]+$`.
- `O-0` sent WP-03 back to A-2/Poincare for repair in the original WP-03 write scope.
- No direct `O-0` implementation edit was made.
- `O-0` then found the existing `mine_palace_lock()` guard in `mempalace.palace` and sent a second WP-03 repair request requiring use of that real per-palace lock for active write refusal.

### 2026-05-05 - WP-03 Acceptance Evidence

- A-2/Poincare changed only `mempalace/mcp_server.py`, `tests/test_mcp_server.py`, and `website/reference/mcp-tools.md`.
- `mempalace_copy_drawer` is registered as an MCP write tool that creates deterministic semantic copies without mutating original `chatgpt_signals` source drawers.
- Deterministic copy IDs are derived from source drawer ID plus canonical `wing:room`, and rerunning the same accepted route returns a no-op success when content hashes match.
- Copied drawers preserve source content and source scalar metadata while adding flat `ontology_*` provenance metadata required by the artifact contract.
- Canonical target `wing`/`room` values are rejected unless they already match lowercase slug-safe ontology keys `^[a-z0-9_]+$`.
- The copy path now takes the existing `mine_palace_lock(_config.palace_path)` before Chroma reads/writes and returns a structured failure without writing if another palace writer holds the lock.
- Tests cover deterministic ID behavior, source preservation, repeated-copy no-op, source metadata provenance, non-slug rejection, non-string run ID rejection, content-hash collision, nested metadata rejection, and palace-lock refusal.
- `O-0` ran `.venv/bin/python -m pytest -q tests/test_mcp_server.py -k "copy_drawer or export_drawers or get_drawer_does_not_leak_absolute_source_file_path or tools_list"`: `13 passed, 72 deselected`.
- `O-0` ran `.venv/bin/python -m py_compile mempalace/mcp_server.py tests/test_mcp_server.py`: passed.
- `O-0` ran `git diff --check -- mempalace/mcp_server.py tests/test_mcp_server.py website/reference/mcp-tools.md docs/worksheets/mempalace_chatgpt_signal_ontology_worksheet_2026-05-05.md`: passed.
- Residual limitation: palace-lock refusal covers writers that honor the existing per-palace lock; it does not detect unrelated processes that bypass the lock.
- Checkpoint D is green.

### 2026-05-05 - WP-03 Milestone Commit Evidence

- `git add mempalace/mcp_server.py tests/test_mcp_server.py website/reference/mcp-tools.md docs/worksheets/mempalace_chatgpt_signal_ontology_worksheet_2026-05-05.md` staged only accepted WP-03 files plus worksheet status.
- `git diff --cached --check` passed.
- `git commit -m "Add idempotent ontology drawer copy"` created `5c611f3`.
- `git push git@github.com:botman058/mempalace.git HEAD:refs/heads/codex/mempalace-http-mcp-closure` pushed `5c611f3` to the fork branch.
- Active WP-06/WP-13 files, unaccepted `docs/reference/`, and out-of-scope `.agents/plugins/marketplace.json` were not staged.

### 2026-05-05 - WP-06 and WP-13 Activation

- `O-0` reread this worksheet before activation.
- WP-06 was assigned to A-1/Faraday with model `gpt-5.4` and reasoning depth `high`.
- A-1/Faraday write scope is limited to a pure pass1 prompt/parser module and focused tests; A-1 is forbidden from editing active WP-03 files, dashboard code, `.agents/plugins/marketplace.json`, `docs/reference/`, or this worksheet.
- WP-13 was assigned to A-4/Rawls with model `gpt-5.4-mini` and reasoning depth `medium`.
- A-4/Rawls write scope is limited to `mempalace/dashboard_server.py`, `tests/test_dashboard_server.py`, and an optional small note in `website/guide/dashboard.md`; A-4 is forbidden from editing dashboard UI static assets, active WP-03 files, `.agents/plugins/marketplace.json`, `docs/reference/`, or this worksheet.
- WP-06 and WP-13 are non-conflicting with WP-03 repair and with each other.

### 2026-05-05 - WP-06 Review Repair Request

- A-1/Faraday returned a scoped WP-06 patch adding `mempalace/ontology_pass1.py` and `tests/test_ontology_pass1.py`.
- `O-0` ran `.venv/bin/python -m pytest -q tests/test_ontology_pass1.py`: `7 passed`.
- `O-0` ran `.venv/bin/python -m ruff check mempalace/ontology_pass1.py tests/test_ontology_pass1.py`: passed.
- `O-0` ran `.venv/bin/python -m py_compile mempalace/ontology_pass1.py tests/test_ontology_pass1.py`: passed.
- `O-0` sent WP-06 back for narrow repair: malformed provider response shapes must become `invalid_model_output` phase records instead of crashing, and tests must include concrete sample `pass1_open` JSONL serialization evidence.

### 2026-05-05 - WP-06 Acceptance Evidence

- A-1/Faraday repaired the pass1 parser so non-text provider responses become `record_status: "invalid_model_output"` with `error_code: "invalid_response_text"`, a bounded raw excerpt, and `retryable: true`.
- `mempalace/ontology_pass1.py` now builds a LocalAI/OpenAI-compatible prompt for one source drawer and returns JSONL-ready `ontology.phase_record` dictionaries for the `pass1_open` phase.
- Valid model output maps to open-ended `payload.proposed_wing` and `payload.proposed_room`; these are hypotheses for later clustering, not canonical final routes.
- Invalid JSON, missing keys, invalid slug keys, invalid response shapes, and malformed non-text responses become durable invalid-output phase records instead of crashing.
- Tests cover valid parse, invalid JSON, missing room key, non-slug wing/room rejection, code-fenced/prose-wrapped JSON extraction, bounded raw excerpts, JSONL round-trip serialization, and fake-provider classification.
- `O-0` ran `.venv/bin/python -m pytest -q tests/test_ontology_pass1.py`: `10 passed`.
- `O-0` ran `.venv/bin/python -m ruff check mempalace/ontology_pass1.py tests/test_ontology_pass1.py`: passed.
- `O-0` ran `.venv/bin/python -m py_compile mempalace/ontology_pass1.py tests/test_ontology_pass1.py`: passed.
- `O-0` ran `git diff --check -- mempalace/ontology_pass1.py tests/test_ontology_pass1.py docs/worksheets/mempalace_chatgpt_signal_ontology_worksheet_2026-05-05.md`: passed.
- Known gap: no CLI/run-loop integration yet; this package intentionally exposes pure prompt/parser and record assembly only.
- Checkpoint F is green.

### 2026-05-05 - WP-06 Milestone Commit Evidence

- `git add mempalace/ontology_pass1.py tests/test_ontology_pass1.py docs/worksheets/mempalace_chatgpt_signal_ontology_worksheet_2026-05-05.md` staged only accepted WP-06 files plus worksheet status.
- `git diff --cached --check` passed.
- `git commit -m "Add ChatGPT ontology pass1 parser"` created `76d6014`.
- `git push git@github.com:botman058/mempalace.git HEAD:refs/heads/codex/mempalace-http-mcp-closure` pushed `76d6014` to the fork branch.
- Active WP-13 files, unaccepted `docs/reference/`, and out-of-scope `.agents/plugins/marketplace.json` were not staged.

### 2026-05-05 - WP-07 Activation

- `O-0` reread this worksheet before activation.
- WP-07 was assigned to A-3 with model `gpt-5.4` and reasoning depth `high`.
- A-3 write scope is limited to a pure candidate clustering module and focused tests, preferably `mempalace/ontology_candidates.py` and `tests/test_ontology_candidates.py`.
- A-3 is forbidden from editing active WP-13 files, MCP files, dashboard UI files, `.agents/plugins/marketplace.json`, `docs/reference/`, or this worksheet.

### 2026-05-05 - WP-07 Acceptance Evidence

- A-3/Bernoulli added `mempalace/ontology_candidates.py` and `tests/test_ontology_candidates.py`.
- `cluster_pass1_phase_records()` groups valid `pass1_open` records by `(proposed_wing, proposed_room)` and preserves wing context, so identical room names under different wings remain distinct candidate `wing:room` groups.
- Candidate cluster records are JSONL-ready `ontology.phase_record` entries for `phase: candidate_clusters`, `subject_type: candidate`, and deterministic slug-safe candidate IDs such as `cand_life_admin__appointments_and_forms`.
- Payloads include `candidate_key`, proposed canonical `wing:room`, compact cluster stats, centroid summaries, source drawer refs, and bounded examples for later WP-08 naming/pruning.
- Invalid, wrong-phase, non-ok, mismatched-run, and superseded retry records are skipped or summarized without crashing.
- `O-0` sent one repair for a ruff `F841` unused local; A-3 removed it without broad changes.
- `O-0` ran `.venv/bin/python -m pytest -q tests/test_ontology_candidates.py`: `6 passed`.
- `O-0` ran `.venv/bin/python -m ruff check mempalace/ontology_candidates.py tests/test_ontology_candidates.py`: passed.
- `O-0` ran `.venv/bin/python -m py_compile mempalace/ontology_candidates.py tests/test_ontology_candidates.py`: passed.
- `O-0` ran `git diff --check -- mempalace/ontology_candidates.py tests/test_ontology_candidates.py docs/worksheets/mempalace_chatgpt_signal_ontology_worksheet_2026-05-05.md`: passed.
- Known gap: no CLI/run-loop integration or artifact publishing yet; WP-07 intentionally provides pure clustering and record assembly only.
- WP-07 is complete; Checkpoint G remains in progress until WP-08 canonical candidate naming/pruning is accepted.

### 2026-05-05 - WP-07 Milestone Commit Evidence

- `git add mempalace/ontology_candidates.py tests/test_ontology_candidates.py docs/worksheets/mempalace_chatgpt_signal_ontology_worksheet_2026-05-05.md` staged only accepted WP-07 files plus worksheet status.
- `git diff --cached --check` passed.
- `git commit -m "Add ontology candidate clustering"` created `780297a`.
- `git push git@github.com:botman058/mempalace.git HEAD:refs/heads/codex/mempalace-http-mcp-closure` pushed `780297a` to the fork branch.
- Active WP-14 files, unaccepted `docs/reference/`, and out-of-scope `.agents/plugins/marketplace.json` were not staged.

### 2026-05-05 - WP-13 Review Repair Request

- A-4/Rawls returned a scoped WP-13 patch adding dashboard ontology run endpoints in `mempalace/dashboard_server.py`, tests in `tests/test_dashboard_server.py`, and a dashboard guide note.
- `O-0` ran `.venv/bin/python -m pytest -q tests/test_dashboard_server.py`: `10 passed`.
- `O-0` ran `.venv/bin/python -m py_compile mempalace/dashboard_server.py tests/test_dashboard_server.py`: passed.
- `O-0` observed `.venv/bin/python -m ruff check mempalace/dashboard_server.py tests/test_dashboard_server.py website/guide/dashboard.md` reports `C901 create_app is too complex`; broad complexity refactor is deferred because WP-13 is a read-only endpoint package.
- `O-0` sent WP-13 back for narrow repair: restore equivalent existing overview telemetry test coverage removed by the patch, and make ontology run-root configuration honor the forbidden `/media/u0/Extreme SSD` constraint.

### 2026-05-05 - WP-13 Acceptance Evidence

- A-4/Rawls restored overview telemetry test coverage and changed ontology run-root loading to reuse the existing ontology run-root resolver, which refuses `/media/u0/Extreme SSD`.
- `mempalace/dashboard_server.py` now exposes read-only authenticated endpoints: `GET /api/ontology/runs`, `GET /api/ontology/runs/{run_id}`, `GET /api/ontology/runs/{run_id}/artifacts`, and `GET /api/ontology/runs/{run_id}/unresolved-preview`.
- The endpoints read `progress.json`, `artifacts_index.json`, and bounded unresolved JSONL tails directly from the configured ontology run root; they do not call Chroma, MCP tools, LocalAI, mining, classification, or ontology mutation code.
- Run IDs and artifact relative paths are validated to block traversal, and unresolved previews respect `dashboard_safe` and `privacy_level` metadata.
- Tests cover active, completed, failed, and interrupted run shapes; artifact listing; bounded unresolved previews; authentication; invalid run IDs; mining-active access; no upstream MCP calls; run-root env overrides; forbidden run-root refusal; and existing overview telemetry behavior.
- `website/guide/dashboard.md` documents the new read-only ontology progress API surface.
- `O-0` ran `.venv/bin/python -m pytest -q tests/test_dashboard_server.py`: `12 passed`.
- `O-0` ran `.venv/bin/python -m py_compile mempalace/dashboard_server.py tests/test_dashboard_server.py`: passed.
- `O-0` ran `git diff --check -- mempalace/dashboard_server.py tests/test_dashboard_server.py website/guide/dashboard.md docs/worksheets/mempalace_chatgpt_signal_ontology_worksheet_2026-05-05.md`: passed.
- `O-0` ran `.venv/bin/python -m ruff check --select F401 mempalace/dashboard_server.py tests/test_dashboard_server.py`: passed.
- Residual lint note: full-file ruff still reports `C901 create_app is too complex`; broad dashboard refactor is deferred because it is outside WP-13.
- WP-13 is complete; Checkpoint J remains in progress until WP-14 adds dashboard UI progress/meter coverage.

### 2026-05-05 - WP-13 Milestone Commit Evidence

- `git add mempalace/dashboard_server.py tests/test_dashboard_server.py website/guide/dashboard.md docs/worksheets/mempalace_chatgpt_signal_ontology_worksheet_2026-05-05.md` staged only accepted WP-13 files plus worksheet status.
- `git diff --cached --check` passed.
- `git commit -m "Add ontology progress dashboard endpoints"` created `fdbf41d`.
- `git push git@github.com:botman058/mempalace.git HEAD:refs/heads/codex/mempalace-http-mcp-closure` pushed `fdbf41d` to the fork branch.
- Active WP-07 work, unaccepted `docs/reference/`, and out-of-scope `.agents/plugins/marketplace.json` were not staged.

### 2026-05-05 - WP-14 Activation

- `O-0` reread this worksheet before activation.
- WP-14 was assigned to A-5 with model `gpt-5.4-mini` and reasoning depth `medium`.
- A-5 write scope is limited to dashboard static UI assets and focused dashboard UI tests if available.
- A-5 is forbidden from editing dashboard backend files, MCP files, ontology algorithm modules, `.agents/plugins/marketplace.json`, `docs/reference/`, or this worksheet.

### 2026-05-05 - WP-08 Activation

- `O-0` reread this worksheet before activation.
- WP-08 was assigned to A-1/Archimedes with model `gpt-5.4` and reasoning depth `high`.
- A-1 write scope is limited to one pure candidate naming/pruning module under `mempalace/` and focused tests under `tests/`.
- A-1 is forbidden from editing CLI/run-loop, MCP, dashboard backend/static files, `.agents/plugins/marketplace.json`, `docs/reference/`, or this worksheet.
- WP-08 is non-conflicting with active WP-14 dashboard static repair.

### 2026-05-05 - WP-14 Acceptance Evidence

- A-5/James changed `mempalace/dashboard_static/app.js`, `mempalace/dashboard_static/index.html`, `mempalace/dashboard_static/styles.css`, and added `tests/test_dashboard_static_contract.py`.
- The static dashboard now shows ontology run selection, current phase progress, a progress bar based on `current_phase_progress.processed / total`, dashboard-safe artifact metadata, and bounded unresolved previews.
- `refreshOverview()` refreshes ontology progress even when `state.miningActive` is true, while search, taxonomy, and drawer browsing remain disabled in telemetry-only mode.
- The ontology UI calls only the read-only WP-13 endpoints and does not call mutation, copy, apply, Chroma, LocalAI, mining, or classification paths.
- `website/guide/dashboard.md` now documents the progress panel, artifact metadata browser, and bounded unresolved preview behavior.
- `CHANGELOG.md` records the dashboard progress panel as part of the ChatGPT signal ontology tranche.
- `O-0` ran `.venv/bin/python -m unittest -v tests.test_dashboard_static_contract`: 5 tests passed.
- `O-0` ran `.venv/bin/python -m pytest -q tests/test_dashboard_static_contract.py tests/test_dashboard_server.py`: 17 passed, 23 subtests passed.
- `O-0` ran `node --check mempalace/dashboard_static/app.js`: passed.
- `O-0` ran `.venv/bin/python -m ruff check tests/test_dashboard_static_contract.py`: passed.
- `O-0` ran `.venv/bin/python -m py_compile tests/test_dashboard_static_contract.py`: passed.
- `O-0` ran `git diff --check -- CHANGELOG.md website/guide/dashboard.md mempalace/dashboard_static/app.js mempalace/dashboard_static/index.html mempalace/dashboard_static/styles.css tests/test_dashboard_static_contract.py docs/worksheets/mempalace_chatgpt_signal_ontology_worksheet_2026-05-05.md`: passed.
- Checkpoint J is green.

### 2026-05-05 - WP-14 Milestone Commit Evidence

- `git add CHANGELOG.md website/guide/dashboard.md mempalace/dashboard_static/app.js mempalace/dashboard_static/index.html mempalace/dashboard_static/styles.css tests/test_dashboard_static_contract.py docs/worksheets/mempalace_chatgpt_signal_ontology_worksheet_2026-05-05.md` staged only accepted WP-14 files plus worksheet status.
- `git diff --cached --check` passed.
- `git commit -m "Add ontology progress dashboard UI"` created `d002072`.
- `git push git@github.com:botman058/mempalace.git HEAD:refs/heads/codex/mempalace-http-mcp-closure` pushed `d002072` to the fork branch.
- Active WP-08 work, unaccepted `docs/reference/`, and out-of-scope `.agents/plugins/marketplace.json` were not staged.

### 2026-05-05 - WP-08 Acceptance Evidence

- A-1/Archimedes added `mempalace/ontology_candidate_names.py` and `tests/test_ontology_candidate_names.py`.
- `build_candidate_naming_prompt()` creates a LocalAI/OpenAI-compatible prompt from WP-07 cluster records and candidate merge choices without network calls.
- `parse_candidate_naming_response()` accepts `keep`, `merge`, and `prune` JSON decisions, validates lowercase slug-safe canonical wing/room keys, validates merge targets against supplied candidate IDs/keys, and preserves wing context for same-named rooms.
- `build_canonical_candidate_records()` emits JSONL-ready `ontology.phase_record` records for `phase: canonical_candidates`, carrying source candidate refs, cluster stats, centroids, source drawer refs, and bounded examples forward.
- Invalid JSON, malformed response shapes, missing required keys, invalid actions, invalid slug keys, invalid merge targets, missing model outputs, non-ok cluster records, and wrong-phase inputs become durable invalid/skipped/error records or skipped summaries without crashing.
- `docs/chatgpt_signal_ontology_artifacts.md` now includes `canonical_candidates` in the phase order and documents candidate naming/pruning phase payloads.
- `CHANGELOG.md` records the candidate naming/pruning helper.
- `O-0` ran `.venv/bin/python -m pytest -q tests/test_ontology_candidate_names.py tests/test_ontology_candidates.py`: 16 passed.
- `O-0` ran `.venv/bin/python -m ruff check mempalace/ontology_candidate_names.py tests/test_ontology_candidate_names.py`: passed.
- `O-0` ran `.venv/bin/python -m py_compile mempalace/ontology_candidate_names.py tests/test_ontology_candidate_names.py`: passed.
- `O-0` ran `git diff --check -- CHANGELOG.md docs/chatgpt_signal_ontology_artifacts.md mempalace/ontology_candidate_names.py tests/test_ontology_candidate_names.py docs/worksheets/mempalace_chatgpt_signal_ontology_worksheet_2026-05-05.md`: passed.
- Known gap: no CLI/run-loop integration or artifact publishing yet; WP-08 intentionally provides pure prompt/parser and record assembly only.
- Checkpoint G is green.

### 2026-05-05 - WP-08 Milestone Commit Evidence

- `git add CHANGELOG.md docs/chatgpt_signal_ontology_artifacts.md mempalace/ontology_candidate_names.py tests/test_ontology_candidate_names.py docs/worksheets/mempalace_chatgpt_signal_ontology_worksheet_2026-05-05.md` staged only accepted WP-08 files plus worksheet status.
- `git diff --cached --check` passed.
- `git commit -m "Add ontology candidate naming records"` created `e6c2906`.
- `git push git@github.com:botman058/mempalace.git HEAD:refs/heads/codex/mempalace-http-mcp-closure` pushed `e6c2906` to the fork branch.
- Unaccepted `docs/reference/` and out-of-scope `.agents/plugins/marketplace.json` were not staged.

### 2026-05-05 - WP-09 Activation

- `O-0` reread this worksheet before activation.
- WP-09 was assigned to A-3/Laplace with model `gpt-5.4` and reasoning depth `high`.
- A-3 write scope is limited to one pure route-candidate retrieval module under `mempalace/` and focused tests under `tests/`.
- A-3 is forbidden from editing CLI/run-loop, MCP, dashboard backend/static files, `.agents/plugins/marketplace.json`, `docs/reference/`, or this worksheet.
- WP-09 is unblocked by Checkpoint G and will feed WP-10 route prompt/parser.

### 2026-05-05 - WP-09 Reassignment

- A-3/Laplace exceeded the small-package window, did not respond to a bounded status request, and landed no scoped files in the shared worktree.
- `O-0` closed A-3/Laplace without accepting output.
- Replacement A-3R/Kepler was assigned WP-09 with model `gpt-5.4` and reasoning depth `high`.
- A-3R write scope remains limited to `mempalace/ontology_route_candidates.py` and `tests/test_ontology_route_candidates.py`.
- A-3R was instructed to deliver the smallest useful deterministic candidate index, top-k selector, and JSONL-ready `route_candidates` records.

### 2026-05-05 - WP-09 Acceptance Evidence

- A-3R/Kepler added `mempalace/ontology_route_candidates.py` and `tests/test_ontology_route_candidates.py`.
- `build_candidate_index()` normalizes WP-08 `canonical_candidates` records, excludes pruned candidates, resolves merge records onto the terminal kept candidate, and preserves distinct `wing:room` identities for same-named rooms.
- `select_route_candidates_for_drawer()` ranks candidates with deterministic local lexical scoring from drawer text/title/metadata plus candidate label, definition, source rooms, and examples; it returns up to five candidates.
- `build_route_candidate_records()` emits JSONL-ready `ontology.phase_record` records for `phase: route_candidates`, `subject_type: drawer`, with ranked candidate shortlist provenance and bounded drawer excerpts.
- Empty candidate indexes, no plausible matches, invalid drawers, invalid canonical records, non-ok canonical records, and wrong-phase inputs produce durable skipped/ok/error records or skipped summaries without crashing.
- `docs/chatgpt_signal_ontology_artifacts.md` now includes `route_candidates` in the phase order and documents the shortlist payload.
- `CHANGELOG.md` records the route-candidate retrieval helper.
- `O-0` ran `.venv/bin/python -m pytest -q tests/test_ontology_route_candidates.py tests/test_ontology_candidate_names.py tests/test_ontology_candidates.py`: 22 passed.
- `O-0` ran `.venv/bin/python -m ruff check mempalace/ontology_route_candidates.py tests/test_ontology_route_candidates.py`: passed.
- `O-0` ran `.venv/bin/python -m py_compile mempalace/ontology_route_candidates.py tests/test_ontology_route_candidates.py`: passed.
- `O-0` ran `git diff --check -- CHANGELOG.md docs/chatgpt_signal_ontology_artifacts.md mempalace/ontology_route_candidates.py tests/test_ontology_route_candidates.py docs/worksheets/mempalace_chatgpt_signal_ontology_worksheet_2026-05-05.md`: passed.
- Known gap: no CLI/run-loop integration or artifact publishing yet; WP-09 intentionally provides pure deterministic retrieval and record assembly only.
- Checkpoint H remains in progress until WP-10 route prompt/parser is accepted.

### 2026-05-05 - WP-09 Milestone Commit Evidence

- `git add CHANGELOG.md docs/chatgpt_signal_ontology_artifacts.md mempalace/ontology_route_candidates.py tests/test_ontology_route_candidates.py docs/worksheets/mempalace_chatgpt_signal_ontology_worksheet_2026-05-05.md` staged only accepted WP-09 files plus worksheet status.
- `git diff --cached --check` passed.
- `git commit -m "Add ontology route candidate retrieval"` created `701ba4a`.
- `git push git@github.com:botman058/mempalace.git HEAD:refs/heads/codex/mempalace-http-mcp-closure` pushed `701ba4a` to the fork branch.
- Unaccepted `docs/reference/` and out-of-scope `.agents/plugins/marketplace.json` were not staged.

### 2026-05-05 - WP-04 Acceptance Evidence

- B-2 changed `mempalace/cli.py`, added `mempalace/ontology_run.py`, and added `tests/test_ontology_cli.py`.
- `mempalace ontology chatgpt-signals` is dry-run by default and accepts `--source-wing`, `--run-dir`, and `--run-id`.
- The shell validates run IDs, refuses `/media/u0/Extreme SSD`, and creates only a minimal run directory plus `run_metadata.json` when `--no-dry-run` is used.
- `O-0` reviewed the diff and found no LocalAI, Chroma, MCP, copy/apply, or ontology processing behavior in WP-04.
- `python3 -m compileall mempalace/cli.py mempalace/ontology_run.py tests/test_ontology_cli.py` passed.
- Manual dry-run CLI smoke printed the resolved default run directory and did not create the default ontology run.
- Manual non-dry-run shell smoke against a temporary directory created a run directory and `run_metadata.json` with schema `ontology.run_shell`.
- `python3 -m pytest tests/test_ontology_cli.py -q` could not run locally because `tests/conftest.py` imports missing `chromadb`.
- `git diff --check -- mempalace/cli.py mempalace/ontology_run.py tests/test_ontology_cli.py` passed.

### 2026-05-05 - WP-04 Milestone Commit Evidence

- `git add mempalace/cli.py mempalace/ontology_run.py tests/test_ontology_cli.py docs/worksheets/mempalace_chatgpt_signal_ontology_worksheet_2026-05-05.md` staged only accepted WP-04 files plus worksheet status.
- `git diff --cached --check` passed.
- `git commit -m "Add ChatGPT ontology run shell"` created `0b76d77`.
- `git push git@github.com:botman058/mempalace.git HEAD:refs/heads/codex/mempalace-http-mcp-closure` pushed `0b76d77` to the fork branch.
- Active WP-02 files, unaccepted `docs/reference/`, and out-of-scope `.agents/plugins/marketplace.json` were not staged.
