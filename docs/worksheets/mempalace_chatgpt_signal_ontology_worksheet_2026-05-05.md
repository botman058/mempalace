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
| C - Source Export Green | pending | Unblocked by WP-01. | WP-02 |
| D - Semantic Copy Green | blocked | Requires WP-02 then WP-03. | WP-03 |
| E - Progressive Run Green | pending | WP-04 and WP-05 unblocked by WP-01. | WP-04/WP-05 |
| F - Pass1 Candidate Green | blocked | Requires WP-06. | WP-06 |
| G - Canonical Candidate Green | blocked | Requires WP-07 and WP-08. | WP-07/WP-08 |
| H - Routing Green | blocked | Requires WP-09 and WP-10. | WP-09/WP-10 |
| I - Verification And Iteration Green | blocked | Requires WP-11 and WP-12. | WP-11/WP-12 |
| J - Dashboard Progress Green | blocked | Requires WP-13 and WP-14. | WP-13/WP-14 |
| K - Release Green | blocked | Requires WP-17 and WP-18. | WP-17/WP-18 |

---

## package status ledger

| Package | Status | Owner | Notes |
|---|---|---|---|
| WP-00 | complete | O-0 | Worksheet saved and baseline frozen. |
| WP-01 | complete | A-1R | Artifact/progress schema contract accepted at Checkpoint B. |
| WP-02 | pending | A-2 | Safe source drawer export. |
| WP-03 | blocked | A-2 | Idempotent semantic copy support. |
| WP-04 | blocked | B-2 | CLI shell and run lifecycle. |
| WP-05 | blocked | B-2 | Progressive materialization and resume markers. |
| WP-06 | blocked | A-1 | Pass1 LocalAI prompt/parser. |
| WP-07 | blocked | A-3 | Candidate clustering. |
| WP-08 | blocked | A-1 | Candidate naming/pruning. |
| WP-09 | blocked | A-3 | Route candidate retrieval. |
| WP-10 | blocked | A-1 | Pass2 route prompt/parser. |
| WP-11 | blocked | A-1 | Local verification pass. |
| WP-12 | blocked | A-3 | Iteration controller and convergence reports. |
| WP-13 | blocked | A-4 | Dashboard progress endpoints. |
| WP-14 | blocked | A-5 | Dashboard progress meter and artifact browser. |
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
