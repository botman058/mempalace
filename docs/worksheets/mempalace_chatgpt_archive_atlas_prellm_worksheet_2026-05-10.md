# MemPalace ChatGPT Archive Atlas Preprocessing - Orchestrated Worksheet
Date: 2026-05-10
Repo baseline: `/home/u4/repos/mempalace`
Live branch baseline: `codex/mempalace-http-mcp-closure` at `64d9406`
Observed branch relation: local checkout on closure branch; out-of-scope dirty `.agents/plugins/marketplace.json`; unaccepted untracked `docs/reference/` remains present
Document type: implementation worksheet
Objective: replace the stopped generic LocalAI chunk-grind with a full-corpus, pre-LLM ChatGPT archive atlas that discovers conversation/thread topic structure from source metadata, lexical evidence, local CUDA embeddings, conservative clustering, and Markdown/JSONL review artifacts without publishing drawers or mutating palace data.

---

## control plane

### Top-level orchestrator

- **Only top-level orchestrator:** `O-0`
- **Model:** `gpt-5.5`
- **Reasoning depth:** `xhigh`
- **Authority:** assign packages, enforce mutation lock, manage parallel worker lanes, review evidence, arbitrate architecture, integrate accepted patches, update worksheet/devlog/docs truth, commit, push milestones, and perform explicitly scoped live service operations on `snow-white-iii`
- **Forbidden uses:** direct package implementation, deleting files or palace data, mutating existing palace drawers, publishing atlas artifacts as drawers, touching `.agents/plugins/marketplace.json`, staging unaccepted `docs/reference/`, using `/media/u0/Extreme SSD`, cloud LLM calls, or restarting the stopped LocalAI grind without a new worksheet gate
- **Mutation lock:** `O-0` is read/review/orchestrate-only by default. Direct implementation edits are forbidden except in declared worksheet/status, integration, or emergency repair mode.

### Working rule

One new worksheet controls this tranche:

`docs/worksheets/mempalace_chatgpt_archive_atlas_prellm_worksheet_2026-05-10.md`

`O-0` rereads this worksheet before package activation, worker acceptance, checkpoint closure, live service operations, docs/devlog updates, staging, commit, and push.

All subagents must be spawned with explicit model and reasoning depth. `O-0` must not let workers inherit model size or reasoning depth by default.

### Current hard gate

Checkpoint A is the active gate. `WP-00` worksheet creation is the only mutation allowed before Checkpoint A is green. No atlas code, tests, runner, systemd wrapper, remote run, or documentation change may start before WP-00 closes.

---

## reasoning-depth matrix

| Model | Reasoning depth | Intended uses | Forbidden uses |
|---|---:|---|---|
| `gpt-5.5` | `xhigh` | `O-0` orchestration, checkpoint verdicts, architecture arbitration | direct package implementation outside declared mutation modes |
| `gpt-5.5` | `high` | atlas contract lead, independent safety review | bounded coding helper work |
| `gpt-5.4` | `high` | source topology, topic evidence, clustering design leads | final safety review of own implementation |
| `gpt-5.3-codex` | `medium` | bounded implementation workers with explicit file ownership | architecture arbitration or broad redesign |
| `gpt-5.3-codex-spark` | `high` | fast fixtures, targeted tests, syntax/static verification, artifact-shape checks | package leadership or safety arbitration |
| `gpt-5.4-mini` | `medium` | docs/operator wording, small report formatting helpers | core atlas architecture |

---

## standing constraints

1. Do not delete files or palace data without explicit confirmation.
2. Do not mutate existing `chatgpt`, `chatgpt_signals`, or partial `chatgpt_thread_signals` artifacts.
3. Do not publish atlas output as drawers in this tranche.
4. Do not use LocalAI or any cloud LLM in this tranche.
5. Do not overwrite outside explicitly designated working folders.
6. Canonical remote root remains `/media/u0/OneDrive_Backup/mempalace`.
7. Atlas run artifacts must live under `/media/u0/OneDrive_Backup/mempalace/data/chatgpt_archive_atlas/<run_id>/`.
8. Do not use `/media/u0/Extreme SSD`.
9. Long remote work runs on `snow-white-iii` as service user `mempalace`.
10. CPU cap target remains 200%; memory cap target remains 16G.
11. Use local embeddings with `MEMPALACE_EMBEDDING_DEVICE=cuda` where available; record effective device.
12. Preserve stopped-grind artifacts as diagnostic evidence only.
13. Do not stage or modify `.agents/plugins/marketplace.json`.
14. Do not stage, rewrite, or delete unaccepted `docs/reference/`.
15. Push accepted milestones to `git@github.com:botman058/mempalace.git HEAD:refs/heads/codex/mempalace-http-mcp-closure`.

---

## O-0 mutation lock

`O-0` is read/review/orchestrate-only until a package has explicit activation, bounded worker ownership, returned implementation evidence, required independent review, and an `O-0` checkpoint verdict.

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

- Prior generic LocalAI grind unit `mempalace-localai-chatgpt-thread-signals-20260510020609.service` is stopped: `inactive/dead`.
- Prior grind produced no `reconciled_signals.jsonl` and no `publish_checkpoint.jsonl`; no bad layer was published.
- Partial grind artifacts remain in `/media/u0/OneDrive_Backup/mempalace/data/localai_chatgpt_thread_signals/20260506031028_thread_signal_rebuild/` and are diagnostic-only.
- ChatGPT source exports live under `/media/u0/OneDrive_Backup/mempalace/sources/chatgpt`.
- Staged ChatGPT source tree contains `19` `conversations.json` files.
- Existing code has reusable selected-path extraction in `mempalace.normalize` and identity helpers in `mempalace.chatgpt_identity`.
- Existing `mempalace.chatgpt_thread_segments` proves useful coverage mechanics but weak topic labels; its stopword/token labeler must not become final atlas labeling.
- Existing `mempalace.embedding` supports ONNX embeddings with CUDA/CoreML/DML/CPU resolution.
- First review surface is JSONL plus Markdown, not dashboard UI.
- First clustering bias is conservative split, not broad merge.

---

## agent pool

| ID | Model | Depth | Role | Intended use | Forbidden use |
|---|---|---:|---|---|---|
| `O-0` | `gpt-5.5` | xhigh | Owner/orchestrator | assign, review, checkpoint, integrate, update worksheet/status | implementation lead or direct package coding |
| `L-1` | `gpt-5.5` | high | Atlas contract lead | artifact schemas, invariants, no-write contract, acceptance contract | parser or runner implementation |
| `L-2` | `gpt-5.4` | high | Source topology lead | ChatGPT export structure, selected path, metadata, thread semantics | embedding/clustering implementation |
| `L-3` | `gpt-5.4` | high | Topic evidence lead | lexical/topic policy, domain-token taxonomy, noise rules | source reader implementation |
| `L-4` | `gpt-5.4` | high | Semantic clustering lead | embedding feature design, conservative clustering, cluster evidence contract | safety review of own code |
| `L-5` | `gpt-5.3-codex` | medium | Ops runner lead | snow-white runner, resource caps, service/runbook scripts | atlas schema arbitration |
| `H-1` | `gpt-5.3-codex` | medium | Source parser helper | bounded source reader and conversation index patches | architecture decisions |
| `H-2` | `gpt-5.3-codex` | medium | Thread helper | bounded thread index patches | lexical policy ownership |
| `H-3` | `gpt-5.3-codex` | medium | Sketch helper | bounded lexical sketch implementation | clustering design |
| `H-4` | `gpt-5.3-codex` | medium | Embedding helper | bounded embedding cache implementation | source topology decisions |
| `H-5` | `gpt-5.4-mini` | medium | Report/docs helper | Markdown summary and operator docs | core algorithm implementation |
| `T-1` | `gpt-5.3-codex-spark` | high | Test helper | fixtures, fake embeddings, CLI tests | package leadership |
| `V-1` | `gpt-5.3-codex-spark` | high | Verification helper | syntax, `bash -n`, targeted tests, artifact checks | implementation under review |
| `R-1` | `gpt-5.5` | high | Independent reviewer | no-delete/no-cloud/no-publish/no-palace-write/idempotency review | implementation ownership |

---

## package overview

| Package | Lead | Support | Purpose | Size | Blocked by? | Parallel lane |
|---|---|---|---|---:|---|---|
| WP-00 | `O-0` status-only | none | Create worksheet and freeze baseline | S | none | gate |
| WP-01 | `L-1` | `T-1` | Define atlas artifact contract and schema tests | S | WP-00 | contract |
| WP-02 | `T-1` | `L-2` | Build fixture plan and malformed/export-shape fixtures | S | WP-00 | tests |
| WP-03 | `L-2` | `H-1` | Implement source inventory and safe export loading | S | WP-01 | source |
| WP-04 | `L-2` | `H-1`, `T-1` | Implement conversation index | S | WP-03 | source |
| WP-05 | `L-2` | `H-2`, `T-1` | Implement thread index | M | WP-04 | source |
| WP-06 | `L-3` | `H-3` | Define lexical evidence policy | S | WP-04 | evidence |
| WP-07 | `L-3` | `H-3`, `T-1` | Implement lexical sketches | M | WP-05, WP-06 | evidence |
| WP-08 | `L-4` | `H-4`, `V-1` | Implement embedding cache with CUDA evidence | M | WP-07 | semantic |
| WP-09 | `L-4` | `H-4`, `T-1` | Implement conservative topic clustering | M | WP-08 | semantic |
| WP-10 | `L-3` | `H-5` | Implement Markdown atlas summary | S | WP-09 | report |
| WP-11 | `L-5` | `V-1` | Implement snow-white runner and operator runbook | S | WP-01 | ops |
| WP-12 | `R-1` | `V-1` | Independent safety/contract review | S | WP-09, WP-10, WP-11 | review |
| WP-13 | `L-5` | `O-0`, `V-1` | Bounded remote smoke run | S | WP-12 | live |
| WP-14 | `L-5` | `O-0`, `V-1` | Full archive atlas run | L | WP-13 | live |
| WP-15 | `O-0` status-only | `H-5`, `V-1` | Docs/devlog, integration verdict, commit, push | S | WP-14 | closure |

Parallel activation plan:

- After WP-00: activate WP-01 and WP-02 in parallel.
- After WP-01: activate WP-03 and WP-11 in parallel.
- After WP-04: activate WP-05 and WP-06 in parallel.
- After WP-07: activate WP-08 and WP-10 draft/report scaffolding only if write scopes do not overlap.
- After WP-09/WP-10/WP-11: activate WP-12.
- Full live work remains serialized: WP-13 then WP-14.

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

The atlas runner must materialize progressively:

- `progress.json` after each phase and at bounded intervals during long phases.
- One append-only JSONL per phase.
- `artifacts_index.json` listing artifact key, schema name, relative path, phase, count, and dashboard/review safety.
- `source_file_errors.jsonl` for malformed/truncated source files.
- No terminal-only progress is acceptable.

### Evidence rules

Acceptable evidence:

- schema tests for every emitted artifact type
- tests proving malformed exports are recorded and skipped without crashing
- tests proving selected-path traversal preserves message metadata
- tests proving long first messages and later turns remain reachable
- lexical tests proving `the`/`and`/`you` cannot be primary topic labels
- fake-embedding tests proving deterministic conservative clustering
- CUDA/effective-device evidence from the embedding phase
- smoke run under `snow-white-iii` as `mempalace`
- independent review proving no LocalAI, cloud, MCP write, drawer publish, or palace mutation path

Insufficient evidence:

- worker summary alone
- docs-only schema
- terminal output without artifacts
- broad clusters without representative evidence
- source labels based only on stopword-prone token frequency
- local-only tests for full-run readiness
- any final artifact produced outside the designated atlas run directory
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
- **Required evidence:** worksheet exists on disk; branch/head/status recorded; stopped-grind state recorded; agent pool and package table include explicit leads/support; parallel activation plan recorded.
- **Insufficient evidence:** plan in chat only or compact package sketch.
- **Disposition:** green unlocks WP-01 and WP-02.

### Checkpoint B - Artifact Contract Green

- **Proves:** every atlas output has a durable inspectable contract before implementation spreads.
- **Required evidence:** schema tests for `progress.json`, `artifacts_index.json`, `conversation_index.jsonl`, `thread_index.jsonl`, `lexical_sketches.jsonl`, `thread_embeddings`, `topic_clusters.jsonl`, and `atlas_summary.md`.
- **Insufficient evidence:** prose-only schema or terminal progress.
- **Disposition:** green unlocks WP-03 and WP-11.

### Checkpoint C - Source Index Green

- **Proves:** raw export loading and conversation indexing are deterministic, source-close, and metadata-preserving.
- **Required evidence:** tests for dict/list exports, malformed files, duplicate files, selected path, timestamps, message counts, source hashes, and source-file error records.
- **Insufficient evidence:** transcript-only parsing or manual inspection of one export.
- **Disposition:** green unlocks WP-05 and supports WP-06.

### Checkpoint D - Thread Index Green

- **Proves:** atlas units are conversation/thread records, not arbitrary chunks.
- **Required evidence:** tests for explicit topic switches, mixed conversations, long first user messages, stable thread IDs, and no dropped suffix.
- **Insufficient evidence:** current weak subthread labels accepted as final rooms.
- **Disposition:** green unlocks WP-07.

### Checkpoint E - Lexical Evidence Green

- **Proves:** each thread has useful non-LLM topic evidence.
- **Required evidence:** tests for commands, file paths, URLs/domains, packages, model names, legal citations, capitalized phrases, repeated project terms, and stopword/noise rejection.
- **Insufficient evidence:** raw token frequency alone.
- **Disposition:** green unlocks WP-08.

### Checkpoint F - Embedding Cache Green

- **Proves:** local semantic features are generated without palace writes.
- **Required evidence:** resume/idempotency tests, batch bound tests, effective-device recording, fake embedding unit tests, and no Chroma palace collection writes.
- **Insufficient evidence:** CPU-only run with no device evidence.
- **Disposition:** green unlocks WP-09.

### Checkpoint G - Conservative Clustering Green

- **Proves:** topic map avoids the previous coarse-collapse failure.
- **Required evidence:** deterministic fake-vector tests, conservative split behavior, mixed/noisy flags, stable cluster IDs, representative thread refs, and cluster count summary.
- **Insufficient evidence:** a few broad categories or uninspectable centroid output.
- **Disposition:** green unlocks WP-10 and WP-12.

### Checkpoint H - Review Surface Green

- **Proves:** atlas is human-inspectable before any later LLM mining.
- **Required evidence:** `atlas_summary.md` with candidate wings/rooms, cluster sizes, evidence titles, top terms, representative excerpts, and mixed/noisy clusters.
- **Insufficient evidence:** JSONL only.
- **Disposition:** green participates in WP-12.

### Checkpoint I - Safety Review Green

- **Proves:** implementation cannot publish, mutate palace data, call LocalAI/cloud, or delete artifacts.
- **Required evidence:** independent `R-1` review with file/path evidence and explicit green/amber/red verdict.
- **Insufficient evidence:** worker self-review.
- **Disposition:** green unlocks WP-13.

### Checkpoint J - Bounded Remote Smoke Green

- **Proves:** runner works on `snow-white-iii` under real paths and resource caps.
- **Required evidence:** limited run as `mempalace`, CPU cap 200%, memory cap 16G, effective embedding device recorded, all artifacts emitted, no palace data changes.
- **Insufficient evidence:** local unit tests only.
- **Disposition:** green unlocks WP-14.

### Checkpoint K - Full Atlas Run Green

- **Proves:** full ChatGPT archive atlas has been materialized for review.
- **Required evidence:** completed or cleanly resumable full run, source/conversation/thread/cluster counts, artifact index, summary markdown, error summary, elapsed time, effective embedding device.
- **Insufficient evidence:** partial run without status or missing artifacts.
- **Disposition:** green unlocks WP-15.

### Checkpoint L - Closure Green

- **Proves:** branch truth, docs, and remote are coherent.
- **Required evidence:** worksheet/devlog/docs updated, tests recorded, dirty-file scope preserved, commit created, branch pushed.
- **Insufficient evidence:** uncommitted worksheet or unstated dirty files.
- **Disposition:** tranche closed.

---

## detailed work packages

### WP-00 - Worksheet Creation

- **owner:** `O-0`
- **lead:** `O-0` in worksheet/status mode only
- **support:** none
- **objective:** save this worksheet with exact Tako-required structure and frozen branch truth.
- **why:** no implementation may start until the tranche is controlled by a durable O0 worksheet.
- **files/subsystems:** `docs/worksheets/mempalace_chatgpt_archive_atlas_prellm_worksheet_2026-05-10.md`
- **deliverables:** saved worksheet with header, control plane, reasoning-depth matrix, constraints, mutation lock, preserved baseline, agent pool, package overview, orchestration protocol, checkpoints, detailed WPs, assumptions.
- **acceptance:** Checkpoint A required evidence is present.
- **exit:** Checkpoint A green.

### WP-01 - Atlas Artifact Contract

- **owner:** `O-0`
- **lead:** `L-1`
- **support:** `T-1`
- **objective:** define exact artifact schemas and no-write invariants.
- **why:** implementation must not invent artifact shape ad hoc.
- **files/subsystems:** atlas schema module/tests; no runner implementation.
- **deliverables:** schema validators/builders for progress, artifact index, conversation index, thread index, lexical sketch, embedding metadata, topic cluster, and summary manifest.
- **acceptance:** Checkpoint B schema tests pass; no LocalAI/MCP/palace-write fields exist.
- **exit:** Checkpoint B green.

### WP-02 - Fixture Baseline

- **owner:** `O-0`
- **lead:** `T-1`
- **support:** `L-2`
- **objective:** create small fixtures that represent the export shapes and failure modes.
- **why:** parser/thread workers need shared, cheap test inputs.
- **files/subsystems:** tests/fixtures only.
- **deliverables:** fixtures for list export, single dict export, malformed source, duplicate source identity, explicit topic switch, long first user message, mixed legal/sysadmin/personal thread.
- **acceptance:** fixtures are loaded by tests without touching live source data.
- **exit:** fixtures available for WP-03 through WP-07.

### WP-03 - Source Inventory And Safe Loading

- **owner:** `O-0`
- **lead:** `L-2`
- **support:** `H-1`
- **objective:** load `conversations.json` files, record source identity, and preserve source-file errors.
- **why:** atlas must survive malformed/truncated duplicate exports without crashing or deleting anything.
- **files/subsystems:** source reader module and tests.
- **deliverables:** deterministic source-file iterator, source hash, JSON shape handling, source error rows.
- **acceptance:** malformed files emit `source_file_errors.jsonl` records; valid files yield conversations deterministically.
- **exit:** Checkpoint C partial green for source loading.

### WP-04 - Conversation Index

- **owner:** `O-0`
- **lead:** `L-2`
- **support:** `H-1`, `T-1`
- **objective:** emit one `conversation_index.jsonl` row per valid selected-path conversation.
- **why:** topic discovery starts at conversation metadata, not chunks.
- **files/subsystems:** conversation index builder and tests.
- **deliverables:** rows with logical source id, conversation id/title, source path/hash, create/update times, model/plugin metadata when present, message counts, user/assistant counts, char counts, first user excerpt, top user prompt excerpts.
- **acceptance:** selected-path traversal matches existing normalization semantics and preserves timestamps/metadata.
- **exit:** Checkpoint C green.

### WP-05 - Thread Index

- **owner:** `O-0`
- **lead:** `L-2`
- **support:** `H-2`, `T-1`
- **objective:** emit stable `thread_index.jsonl` records from conversation/message structure.
- **why:** one conversation may carry multiple topics; chunk-level LLM extraction caused noise.
- **files/subsystems:** thread indexing module/tests.
- **deliverables:** stable thread ids, message spans, char spans, time spans, title context, representative user excerpts, weak transition reasons.
- **acceptance:** tests prove no dropped suffix, long first message handling, explicit topic switch handling, deterministic ids.
- **exit:** Checkpoint D green.

### WP-06 - Lexical Evidence Policy

- **owner:** `O-0`
- **lead:** `L-3`
- **support:** `H-3`
- **objective:** define deterministic source-close topic evidence rules.
- **why:** lexical sketches must capture archive-specific terms without generic stopword collapse.
- **files/subsystems:** lexical policy module/tests.
- **deliverables:** stopword/noise lists, token ranking rules, phrase extraction policy, domain extractor list.
- **acceptance:** policy explicitly rejects stopword labels and preserves meaningful domain terms.
- **exit:** unlocks WP-07.

### WP-07 - Lexical Sketches

- **owner:** `O-0`
- **lead:** `L-3`
- **support:** `H-3`, `T-1`
- **objective:** emit `lexical_sketches.jsonl` for each thread.
- **why:** clustering needs auditable non-LLM features.
- **files/subsystems:** sketch builder/tests.
- **deliverables:** top terms, capitalized phrases, commands, paths, URLs/domains, packages, model names, legal citations/statutes/cases, dates, repeated project/person/org candidates.
- **acceptance:** Checkpoint E tests pass; primary label candidates cannot be `the`, `and`, `you`, `for`.
- **exit:** Checkpoint E green.

### WP-08 - Embedding Cache

- **owner:** `O-0`
- **lead:** `L-4`
- **support:** `H-4`, `V-1`
- **objective:** emit local thread embeddings under the atlas run directory.
- **why:** semantic clustering should use local GPU where available without touching palace collections.
- **files/subsystems:** embedding cache module/tests.
- **deliverables:** batched embedding runner using `mempalace.embedding`, effective-device metadata, resume/idempotent cache, bounded memory behavior.
- **acceptance:** Checkpoint F tests pass; no Chroma palace collection writes; effective device is recorded.
- **exit:** Checkpoint F green.

### WP-09 - Conservative Topic Clustering

- **owner:** `O-0`
- **lead:** `L-4`
- **support:** `H-4`, `T-1`
- **objective:** emit `topic_clusters.jsonl` from lexical plus embedding evidence.
- **why:** atlas must discover candidate rooms without repeating broad-collapse failure.
- **files/subsystems:** clustering module/tests.
- **deliverables:** stable cluster ids, candidate wing/room hints, mixed/noisy flags, representative thread refs, centroid evidence, cluster stats.
- **acceptance:** Checkpoint G tests pass with fake vectors and conservative split behavior.
- **exit:** Checkpoint G green.

### WP-10 - Markdown Atlas Summary

- **owner:** `O-0`
- **lead:** `L-3`
- **support:** `H-5`
- **objective:** emit `atlas_summary.md` for human review.
- **why:** user needs to inspect topic map before LLM mining resumes.
- **files/subsystems:** summary generator/docs tests.
- **deliverables:** candidate wings/rooms, cluster sizes, top terms, representative excerpts, mixed/noisy clusters, source/error summaries.
- **acceptance:** Checkpoint H green.
- **exit:** review surface ready.

### WP-11 - Snow-White Runner

- **owner:** `O-0`
- **lead:** `L-5`
- **support:** `V-1`
- **objective:** provide a safe remote runner for bounded and full atlas runs.
- **why:** full archive work belongs on `snow-white-iii`, not this Celeron.
- **files/subsystems:** scripts/systemd runner docs; no algorithm code.
- **deliverables:** wrapper with run root guard, service user, CPU/memory caps, CUDA env, no-publish guard, no-LocalAI guard, no `/media/u0/Extreme SSD`.
- **acceptance:** `bash -n`, dry-run/help tests, path guard tests.
- **exit:** ops path ready for review.

### WP-12 - Independent Safety Review

- **owner:** `O-0`
- **lead:** `R-1`
- **support:** `V-1`
- **objective:** review implementation before live execution.
- **why:** atlas must not mutate palace data or restart the stopped bad grind.
- **files/subsystems:** all atlas modules/scripts/tests.
- **deliverables:** green/amber/red review with file/path evidence.
- **acceptance:** Checkpoint I green.
- **exit:** live smoke may start.

### WP-13 - Bounded Remote Smoke

- **owner:** `O-0`
- **lead:** `L-5`
- **support:** `V-1`
- **objective:** run a limited atlas pass on `snow-white-iii`.
- **why:** prove real paths, permissions, CUDA embedding, and artifact writing before full run.
- **files/subsystems:** live run artifacts only.
- **deliverables:** limited run directory with all required artifacts and summary.
- **acceptance:** Checkpoint J green.
- **exit:** full archive run may start.

### WP-14 - Full Archive Atlas Run

- **owner:** `O-0`
- **lead:** `L-5`
- **support:** `V-1`
- **objective:** run the full pre-LLM atlas over all ChatGPT exports.
- **why:** produce the actual topic map for later LLM-guided mining.
- **files/subsystems:** live run artifacts only.
- **deliverables:** completed or cleanly resumable full run under atlas run root.
- **acceptance:** Checkpoint K green.
- **exit:** closure package may start.

### WP-15 - Closure, Docs, Commit, Push

- **owner:** `O-0`
- **lead:** `O-0` in worksheet/status and integration mode only
- **support:** `H-5`, `V-1`
- **objective:** record final truth, update docs/devlog, commit and push.
- **why:** preserve durable handoff and branch state.
- **files/subsystems:** worksheet, devlog/docs only unless accepted integration requires more.
- **deliverables:** updated worksheet, docs/devlog summary, test/run evidence, commit, push.
- **acceptance:** Checkpoint L green.
- **exit:** tranche closed.

---

## assumptions

- This tranche creates a new worksheet, not an amendment to the stopped thread-signal worksheet.
- The stopped LocalAI extraction artifacts are diagnostic-only and do not feed atlas clustering.
- Full archive atlas run is in scope after bounded smoke and independent safety review.
- Review surface is JSONL plus Markdown; dashboard integration is out of scope for this tranche.
- Clustering bias is conservative split.
- No LLM, LocalAI, MCP write, drawer publish, semantic copy, or cloud API call is used in this tranche.
- Later LLM-guided mining will be planned in a separate worksheet after atlas review.

---

## execution log

### 2026-05-11 - WP-00 / Checkpoint A Green

- `O-0` reread this worksheet before activation.
- Current local branch truth before activation: `codex/mempalace-http-mcp-closure` at `d6cac16`.
- Current dirty files remain out of scope: modified `.agents/plugins/marketplace.json` and untracked `docs/reference/`.
- Live guard check on `snow-white-iii`: `mempalace-localai-chatgpt-thread-signals-20260510020609.service` remains `inactive/dead`.
- Live guard check on preserved stopped-grind run directory: `publish_checkpoint.jsonl` is absent, so no stopped-grind publication was observed.
- Checkpoint A required evidence is present: worksheet exists on disk, branch/head/status are recorded, stopped-grind state is recorded, agent pool and package table include explicit leads/support, and the parallel activation plan is recorded.
- Checkpoint A verdict: green.
- Next allowed activation per worksheet: WP-01 and WP-02 in parallel.

### 2026-05-11 - WP-01 / WP-02 Parallel Activation

- `O-0` reread this worksheet before package activation.
- Activated allowed parallel package set: WP-01 and WP-02.
- WP-01 lead `L-1` was assigned to worker Mendel with model `gpt-5.5` and reasoning depth `high`.
- WP-01 write scope was limited to `mempalace/chatgpt_archive_atlas_contract.py` and `tests/test_chatgpt_archive_atlas_contract.py`.
- WP-01 was forbidden from editing runner/source parser/fixtures/docs/systemd files, `.agents/plugins/marketplace.json`, or `docs/reference/`.
- WP-02 lead `T-1` was assigned to worker Noether with model `gpt-5.3-codex-spark` and reasoning depth `high`.
- WP-02 write scope was limited to `tests/fixtures/chatgpt_archive_atlas/**` and `tests/test_chatgpt_archive_atlas_fixtures.py`.
- WP-02 was forbidden from editing implementation modules, runner scripts, docs, systemd files, `.agents/plugins/marketplace.json`, or `docs/reference/`.

### 2026-05-11 - WP-01 / Checkpoint B Evidence

- `O-0` reread this worksheet before worker acceptance review.
- `L-1` returned changed paths: `mempalace/chatgpt_archive_atlas_contract.py` and `tests/test_chatgpt_archive_atlas_contract.py`.
- WP-01 delivered pure-Python contract builders/validators for `progress.json`, `artifacts_index.json`, `conversation_index.jsonl`, `thread_index.jsonl`, `lexical_sketches.jsonl`, thread embedding metadata rows, `topic_clusters.jsonl`, and `atlas_summary.md` manifest records.
- WP-01 contract enforces JSON-safe deterministic rows, required keys, relative artifact paths, bounded statuses, valid run IDs, and forbidden LocalAI/MCP/Chroma/palace-write field keys.
- `O-0` independently inspected the implementation and tests.
- Worker-reported system `pytest` failure was due missing `chromadb`; project venv tests were used for acceptance.
- `O-0` ran `.venv/bin/python -m pytest -q tests/test_chatgpt_archive_atlas_contract.py tests/test_chatgpt_archive_atlas_fixtures.py`: `40 passed in 0.64s`.
- `O-0` ran `.venv/bin/python -m py_compile mempalace/chatgpt_archive_atlas_contract.py tests/test_chatgpt_archive_atlas_contract.py tests/test_chatgpt_archive_atlas_fixtures.py`: passed.
- `O-0` ran `.venv/bin/ruff check mempalace/chatgpt_archive_atlas_contract.py tests/test_chatgpt_archive_atlas_contract.py tests/test_chatgpt_archive_atlas_fixtures.py`: passed.
- `O-0` ran `git diff --check -- mempalace/chatgpt_archive_atlas_contract.py tests/test_chatgpt_archive_atlas_contract.py tests/test_chatgpt_archive_atlas_fixtures.py tests/fixtures/chatgpt_archive_atlas`: passed.
- Checkpoint B verdict: green.
- Checkpoint B disposition: WP-03 and WP-11 are unlocked after this milestone is committed and pushed.

### 2026-05-11 - WP-02 Fixture Baseline Evidence

- `O-0` reread this worksheet before worker acceptance review.
- `T-1` returned changed paths under `tests/fixtures/chatgpt_archive_atlas/**` and `tests/test_chatgpt_archive_atlas_fixtures.py`.
- Fixture inventory now includes `list_export`, `single_dict_export`, `malformed_source`, `duplicate_source_identity`, `explicit_topic_switch`, `long_first_user_message`, and `mixed_legal_sysadmin_personal`.
- Fixtures are small synthetic JSON files; no live ChatGPT source data was copied into the repo.
- WP-02 tests verify fixture discoverability through `manifest.json`, top-level JSON shapes, malformed JSON behavior, duplicate logical IDs, explicit topic switch marker, long first user turn preservation, and mixed legal/sysadmin/personal domain markers.
- `O-0` independently inspected representative fixtures and confirmed they are synthetic and bounded.
- `O-0` ran `.venv/bin/pytest -q tests/test_chatgpt_archive_atlas_fixtures.py`: `14 passed in 0.40s`.
- WP-02 verdict: green.
- WP-02 exit: fixtures are available for WP-03 through WP-07.

### 2026-05-11 - WP-03 / WP-11 Parallel Activation

- `O-0` reread this worksheet before package activation.
- Current local branch truth before activation: `codex/mempalace-http-mcp-closure` at `b5f8255`.
- Current dirty files remain out of scope: modified `.agents/plugins/marketplace.json` and untracked `docs/reference/`.
- Activated allowed parallel package set after Checkpoint B: WP-03 and WP-11.
- WP-03 lead `L-2` was assigned to worker Nietzsche with model `gpt-5.4` and reasoning depth `high`.
- WP-03 write scope was limited to `mempalace/chatgpt_archive_atlas_source.py` and `tests/test_chatgpt_archive_atlas_source.py`.
- WP-03 was forbidden from editing contract, runner, fixture, docs, systemd, `.agents/plugins/marketplace.json`, or `docs/reference/`.
- WP-11 lead `L-5` was assigned to worker Pascal with model `gpt-5.3-codex` and reasoning depth `medium`.
- WP-11 write scope was limited to `scripts/systemd/start_chatgpt_archive_atlas_snow_white_iii.sh`, `scripts/systemd/README.md`, and `tests/test_chatgpt_archive_atlas_runner.py`.
- WP-11 was forbidden from editing atlas algorithm modules, fixtures, dashboard, MCP, `docs/reference/`, or this worksheet.

### 2026-05-11 - WP-03 Source Inventory Evidence

- `O-0` reread this worksheet before worker acceptance review.
- `L-2` returned changed paths: `mempalace/chatgpt_archive_atlas_source.py` and `tests/test_chatgpt_archive_atlas_source.py`.
- WP-03 delivered sorted `conversations.json` discovery, UTF-8 `errors=replace` loading, deterministic file-level `sha256:` source hashes, safe source-relative paths, source ordinals, top-level shape metadata, and JSON-safe source error rows.
- WP-03 records malformed JSON, wrong top-level shapes, invalid conversation items, and outside-root paths as source errors instead of crashing or deleting source files.
- WP-03 preserves duplicate logical-source identities as distinct loaded records with distinct source ordinals.
- `O-0` independently inspected the implementation and tests.
- `O-0` ran `.venv/bin/python -m pytest -q tests/test_chatgpt_archive_atlas_source.py tests/test_chatgpt_archive_atlas_runner.py`: `12 passed in 0.65s`.
- `O-0` ran `.venv/bin/python -m py_compile mempalace/chatgpt_archive_atlas_source.py tests/test_chatgpt_archive_atlas_source.py tests/test_chatgpt_archive_atlas_runner.py`: passed.
- `O-0` ran `.venv/bin/ruff check mempalace/chatgpt_archive_atlas_source.py tests/test_chatgpt_archive_atlas_source.py tests/test_chatgpt_archive_atlas_runner.py`: passed.
- `O-0` ran `bash -n scripts/systemd/start_chatgpt_archive_atlas_snow_white_iii.sh`: passed.
- WP-03 verdict: green.
- Checkpoint C remains partial: source loading is green, but WP-04 conversation index must close before Checkpoint C is fully green.

### 2026-05-11 - WP-11 Snow-White Runner Evidence

- `O-0` reread this worksheet before worker acceptance review.
- `L-5` returned changed paths: `scripts/systemd/start_chatgpt_archive_atlas_snow_white_iii.sh`, `scripts/systemd/README.md`, and `tests/test_chatgpt_archive_atlas_runner.py`.
- WP-11 delivered an artifact-only `systemd-run` wrapper for `snow-white-iii` with canonical defaults under `/media/u0/OneDrive_Backup/mempalace`, source dir `$ROOT/sources/chatgpt`, run root `$ROOT/data/chatgpt_archive_atlas`, and app path `$ROOT/app`.
- The wrapper runs as `User=mempalace` / `Group=mempalace`, sets `CPUQuota=200%`, `MemoryMax=16G`, and `MEMPALACE_EMBEDDING_DEVICE=cuda`, and refuses `/media/u0/Extreme SSD` paths.
- The wrapper supports `--limit`, `--run-id`, `--run-root`, and `--source-dir`.
- `O-0` rejected the first WP-11 return because default `UNIT` was computed before `--run-id` parsing; `L-5` corrected the issue by deriving the default unit after parsing unless `MEMPALACE_CHATGPT_ARCHIVE_ATLAS_UNIT` is explicitly set.
- `O-0` statically scanned the runner and tests for forbidden LocalAI/MCP/publish surfaces. The only matches were negative/help/test text documenting that those surfaces are absent.
- `O-0` ran `.venv/bin/python -m pytest -q tests/test_chatgpt_archive_atlas_source.py tests/test_chatgpt_archive_atlas_runner.py`: `12 passed in 0.65s`.
- `O-0` ran `bash -n scripts/systemd/start_chatgpt_archive_atlas_snow_white_iii.sh`: passed.
- WP-11 verdict: green.
- WP-11 exit: ops path is ready for later independent safety review; no live remote run was started.

### 2026-05-11 - WP-04 Conversation Index Activation

- `O-0` reread this worksheet before package activation.
- Current local branch truth before activation: `codex/mempalace-http-mcp-closure` at `7536bb0`.
- Current dirty files remain out of scope: modified `.agents/plugins/marketplace.json` and untracked `docs/reference/`.
- Activated WP-04 as the active source-lane package needed to close Checkpoint C.
- WP-04 lead `L-2` remains worker Nietzsche with model `gpt-5.4` and reasoning depth `high`.
- WP-04 implementation write scope for `L-2` is limited to `mempalace/chatgpt_archive_atlas_conversation.py`.
- WP-04 test support `T-1` remains worker Noether with model `gpt-5.3-codex-spark` and reasoning depth `high`.
- WP-04 test write scope for `T-1` is limited to `tests/test_chatgpt_archive_atlas_conversation.py`.
- WP-04 source-parser support `H-1` was assigned to worker Halley with model `gpt-5.3-codex` and reasoning depth `medium` for read-only guidance.
- WP-04 workers were forbidden from editing docs, fixtures, runner, dashboard, MCP, LocalAI, Chroma, palace data paths, `.agents/plugins/marketplace.json`, or `docs/reference/`.
- Shared WP-04 API contract was set as `build_chatgpt_conversation_index_rows(...)`, `build_chatgpt_conversation_index(...)`, and immutable `ChatGPTAtlasConversationIndexResult`.

### 2026-05-11 - WP-04 Conversation Index Evidence

- `O-0` reread this worksheet before worker acceptance review.
- `T-1` returned changed path: `tests/test_chatgpt_archive_atlas_conversation.py`.
- `L-2` returned changed path: `mempalace/chatgpt_archive_atlas_conversation.py`.
- `H-1` returned read-only guidance confirming selected-path semantics: valid `current_node` ancestry first, first-child fallback otherwise, user/assistant text only, and source identity requiring at least two selected messages.
- WP-04 delivered immutable result rows and source-error passthrough for `build_chatgpt_conversation_index(...)`.
- WP-04 conversation rows are emitted through `contract.build_conversation_index_row(...)` and preserve logical source id, conversation id/title, source path/hash/ordinal, create/update times, model/plugin metadata when present, selected-path message counts, char counts, first user excerpt, and deterministic top user prompt excerpts.
- WP-04 tests cover dict/list exports, selected branch traversal, duplicate logical source ids, timestamp string preservation, long first user prompt truncation, model/plugin metadata, source error passthrough, row schema validation, and no-write safety contract.
- `O-0` independently inspected the implementation, tests, and `H-1` acceptance guidance.
- `O-0` ran `.venv/bin/python -m pytest -q tests/test_chatgpt_archive_atlas_conversation.py tests/test_chatgpt_archive_atlas_source.py tests/test_chatgpt_archive_atlas_contract.py tests/test_chatgpt_archive_atlas_fixtures.py`: `56 passed in 1.11s`.
- `O-0` ran `.venv/bin/python -m py_compile mempalace/chatgpt_archive_atlas_conversation.py tests/test_chatgpt_archive_atlas_conversation.py`: passed.
- `O-0` ran `.venv/bin/ruff check mempalace/chatgpt_archive_atlas_conversation.py tests/test_chatgpt_archive_atlas_conversation.py`: passed.
- `O-0` ran `git diff --check -- mempalace/chatgpt_archive_atlas_conversation.py tests/test_chatgpt_archive_atlas_conversation.py docs/worksheets/mempalace_chatgpt_archive_atlas_prellm_worksheet_2026-05-10.md`: passed.
- `O-0` statically scanned WP-04 code/tests for LocalAI, MCP, publish, drawer, palace write, Chroma, `/media/u0/Extreme SSD`, and delete/remove surfaces; matches were limited to worksheet constraint text.
- WP-04 verdict: green.
- Checkpoint C verdict: green after WP-03 source loading and WP-04 conversation indexing.
- Checkpoint C disposition: WP-05 and WP-06 are unlocked after this milestone is committed and pushed.

### 2026-05-11 - WP-05 / WP-06 Parallel Activation

- `O-0` reread this worksheet before package activation.
- Current local branch truth before activation: `codex/mempalace-http-mcp-closure` at `87e8444`.
- Current dirty files remain out of scope: modified `.agents/plugins/marketplace.json` and untracked `docs/reference/`.
- Activated allowed parallel package set after Checkpoint C: WP-05 and WP-06.
- WP-05 lead `L-2` remains worker Nietzsche with model `gpt-5.4` and reasoning depth `high`.
- WP-05 implementation write scope for `L-2` is limited to `mempalace/chatgpt_archive_atlas_thread.py`.
- WP-05 test support `T-1` remains worker Noether with model `gpt-5.3-codex-spark` and reasoning depth `high`.
- WP-05 test write scope for `T-1` is limited to `tests/test_chatgpt_archive_atlas_thread.py`.
- WP-05 thread-helper support `H-2` was assigned to worker Pasteur with model `gpt-5.3-codex` and reasoning depth `medium` for read-only guidance.
- WP-06 lead `L-3` was assigned to worker Euclid with model `gpt-5.4` and reasoning depth `high`.
- WP-06 implementation write scope for `L-3` is limited to `mempalace/chatgpt_archive_atlas_lexical_policy.py`.
- WP-06 helper `H-3` was assigned to worker Godel with model `gpt-5.3-codex` and reasoning depth `medium`.
- WP-06 test write scope for `H-3` is limited to `tests/test_chatgpt_archive_atlas_lexical_policy.py`.
- WP-05/WP-06 workers were forbidden from editing docs, fixtures, runner, dashboard, MCP, LocalAI, Chroma, palace data paths, `.agents/plugins/marketplace.json`, or `docs/reference/`.

### 2026-05-11 - WP-05 Thread Index Evidence

- `O-0` reread this worksheet before worker acceptance review.
- `L-2` returned changed path: `mempalace/chatgpt_archive_atlas_thread.py`.
- `T-1` returned changed path: `tests/test_chatgpt_archive_atlas_thread.py`.
- `H-2` returned read-only guidance confirming safe reuse of selected-path extraction and warning not to treat prior weak subthread labels as final taxonomy.
- WP-05 delivered deterministic thread index rows with stable thread ids, thread indexes, selected-path message spans, transcript char spans, user/assistant counts, full-span char counts, title hints, representative excerpts, transition reasons, and source-error passthrough.
- WP-05 tests cover single full-path thread emission, explicit topic switch splitting, mixed legal/sysadmin/personal splitting, long first user prompt coverage, no dropped suffix, stable ids, row schema validation, safety contract, and source-error passthrough.
- `O-0` independently inspected the implementation, tests, and `H-2` acceptance guidance.
- `O-0` ran `.venv/bin/python -m pytest -q tests/test_chatgpt_archive_atlas_thread.py`: `7 passed in 0.43s`.
- `O-0` ran `.venv/bin/python -m py_compile mempalace/chatgpt_archive_atlas_thread.py tests/test_chatgpt_archive_atlas_thread.py`: passed.
- `O-0` ran `.venv/bin/ruff check mempalace/chatgpt_archive_atlas_thread.py tests/test_chatgpt_archive_atlas_thread.py`: passed.
- `O-0` statically scanned WP-05 code/tests for LocalAI, MCP, publish, drawer, palace write, Chroma, `/media/u0/Extreme SSD`, and delete/remove surfaces: no matches.
- WP-05 verdict: green.
- Checkpoint D verdict: green.

### 2026-05-11 - WP-06 Lexical Evidence Policy Evidence

- `O-0` reread this worksheet before worker acceptance review.
- `L-3` returned changed path: `mempalace/chatgpt_archive_atlas_lexical_policy.py`.
- `H-3` returned changed path: `tests/test_chatgpt_archive_atlas_lexical_policy.py`.
- WP-06 delivered deterministic pure-Python lexical policy extraction for top terms, keyphrases, domains, paths, commands, package names, model names, legal citations, capitalized phrases, and rejected noise terms.
- WP-06 tests cover stopword/noise rejection, repeated project/domain term preservation, commands, paths, URL domains, package names, model names, legal citations, capitalized phrases, deterministic bounds, JSON-safe dataclass output, and public API shape.
- `O-0` independently inspected the implementation and tests.
- `O-0` ran `.venv/bin/python -m pytest -q tests/test_chatgpt_archive_atlas_thread.py tests/test_chatgpt_archive_atlas_lexical_policy.py tests/test_chatgpt_archive_atlas_conversation.py tests/test_chatgpt_archive_atlas_source.py tests/test_chatgpt_archive_atlas_contract.py tests/test_chatgpt_archive_atlas_fixtures.py`: `68 passed in 1.64s`.
- `O-0` ran `.venv/bin/python -m py_compile mempalace/chatgpt_archive_atlas_thread.py tests/test_chatgpt_archive_atlas_thread.py mempalace/chatgpt_archive_atlas_lexical_policy.py tests/test_chatgpt_archive_atlas_lexical_policy.py`: passed.
- `O-0` ran `.venv/bin/ruff check mempalace/chatgpt_archive_atlas_thread.py tests/test_chatgpt_archive_atlas_thread.py mempalace/chatgpt_archive_atlas_lexical_policy.py tests/test_chatgpt_archive_atlas_lexical_policy.py`: passed.
- `O-0` ran `git diff --check -- mempalace/chatgpt_archive_atlas_thread.py tests/test_chatgpt_archive_atlas_thread.py mempalace/chatgpt_archive_atlas_lexical_policy.py tests/test_chatgpt_archive_atlas_lexical_policy.py docs/worksheets/mempalace_chatgpt_archive_atlas_prellm_worksheet_2026-05-10.md`: passed.
- `O-0` statically scanned WP-06 code/tests for LocalAI, MCP, publish, drawer, palace write, Chroma, `/media/u0/Extreme SSD`, and delete/remove surfaces: no matches.
- WP-06 verdict: green.
- WP-06 disposition: WP-07 is unlocked after this milestone is committed and pushed.

### 2026-05-11 - WP-07 Lexical Sketch Activation

- `O-0` reread this worksheet before package activation.
- Current local branch truth before activation: `codex/mempalace-http-mcp-closure` at `ab553e5`.
- Current dirty files remain out of scope: modified `.agents/plugins/marketplace.json` and untracked `docs/reference/`.
- Activated WP-07 as the active evidence-lane package needed to close Checkpoint E.
- WP-07 lead `L-3` remains worker Euclid with model `gpt-5.4` and reasoning depth `high`.
- WP-07 implementation write scope for `L-3` is limited to `mempalace/chatgpt_archive_atlas_lexical_sketch.py`.
- WP-07 helper `H-3` remains worker Godel with model `gpt-5.3-codex` and reasoning depth `medium`.
- WP-07 test write scope for `H-3` is limited to `tests/test_chatgpt_archive_atlas_lexical_sketch.py`.
- WP-07 support `T-1` remains worker Noether with model `gpt-5.3-codex-spark` and reasoning depth `high` for read-only acceptance guidance.
- WP-07 workers were forbidden from editing docs, fixtures, runner, dashboard, MCP, LocalAI, Chroma, palace data paths, `.agents/plugins/marketplace.json`, or `docs/reference/`.
- Shared WP-07 API contract was set as `build_chatgpt_lexical_sketch_rows(...)`, `build_chatgpt_lexical_sketches(...)`, and immutable `ChatGPTAtlasLexicalSketchResult`.

### 2026-05-11 - WP-07 Lexical Sketch Evidence

- `O-0` reread this worksheet before worker acceptance review.
- `L-3` returned changed path: `mempalace/chatgpt_archive_atlas_lexical_sketch.py`.
- `H-3` returned changed path: `tests/test_chatgpt_archive_atlas_lexical_sketch.py`.
- `T-1` returned read-only acceptance guidance requiring strict one lexical sketch row per thread row, deterministic row identity, row schema validation, and no service/write surfaces.
- `O-0` rejected the first WP-07 return because source-record matching required non-empty `conversation_id` and keyed only on logical source id, conversation id, and source hash.
- `L-3` corrected matching to include logical source id, optional conversation id, source hash, source relative path, and source ordinal.
- `H-3` added regression coverage for missing top-level conversation id and duplicate logical-source identity mapping.
- WP-07 delivered lexical sketch rows by reconstructing the selected-path transcript, slicing text by WP-05 thread char spans, applying the WP-06 lexical policy, and emitting rows through `contract.build_lexical_sketch_row(...)`.
- WP-07 rows include required lexical evidence plus JSON-safe source/thread metadata, dates, project terms, and person/org candidates.
- WP-07 tests cover one sketch row per thread row, mixed legal/sysadmin/personal evidence, synthetic domains/packages/models/project terms, stopword rejection, deterministic bounds, source-error passthrough, missing conversation id, and duplicate logical identity.
- `O-0` independently inspected the implementation, tests, and `T-1` acceptance guidance.
- `O-0` ran `.venv/bin/python -m pytest -q tests/test_chatgpt_archive_atlas_lexical_sketch.py tests/test_chatgpt_archive_atlas_thread.py tests/test_chatgpt_archive_atlas_lexical_policy.py tests/test_chatgpt_archive_atlas_conversation.py tests/test_chatgpt_archive_atlas_source.py tests/test_chatgpt_archive_atlas_contract.py tests/test_chatgpt_archive_atlas_fixtures.py`: `77 passed in 1.88s`.
- `O-0` ran `.venv/bin/python -m py_compile mempalace/chatgpt_archive_atlas_lexical_sketch.py tests/test_chatgpt_archive_atlas_lexical_sketch.py`: passed.
- `O-0` ran `.venv/bin/ruff check mempalace/chatgpt_archive_atlas_lexical_sketch.py tests/test_chatgpt_archive_atlas_lexical_sketch.py`: passed.
- `O-0` ran `git diff --check -- mempalace/chatgpt_archive_atlas_lexical_sketch.py tests/test_chatgpt_archive_atlas_lexical_sketch.py docs/worksheets/mempalace_chatgpt_archive_atlas_prellm_worksheet_2026-05-10.md`: passed.
- `O-0` statically scanned WP-07 code/tests for LocalAI, MCP, publish, drawer, palace write, Chroma, `/media/u0/Extreme SSD`, delete/remove surfaces, `requests`, `httpx`, and `openai`; matches were limited to synthetic test strings proving domain/package extraction.
- WP-07 verdict: green.
- Checkpoint E verdict: green.
- Checkpoint E disposition: WP-08 is unlocked after this milestone is committed and pushed.

### 2026-05-11 - WP-08 Embedding Cache Activation

- `O-0` reread this worksheet before package activation.
- Current local branch truth before activation: `codex/mempalace-http-mcp-closure` at `dc8c253`.
- Current dirty files remain out of scope: modified `.agents/plugins/marketplace.json` and untracked `docs/reference/`.
- Activated WP-08 as the active semantic-lane package needed to close Checkpoint F.
- WP-08 lead `L-4` was assigned to worker Banach with model `gpt-5.4` and reasoning depth `high`.
- WP-08 implementation write scope for `L-4` is limited to `mempalace/chatgpt_archive_atlas_embedding_cache.py`.
- WP-08 helper `H-4` was assigned to worker Dirac with model `gpt-5.3-codex` and reasoning depth `medium`.
- WP-08 test write scope for `H-4` is limited to `tests/test_chatgpt_archive_atlas_embedding_cache.py`.
- WP-08 verification support `V-1` was assigned to worker Jason with model `gpt-5.3-codex-spark` and reasoning depth `high` for read-only acceptance guidance.
- WP-08 workers were forbidden from editing docs, fixtures, runner, dashboard, MCP, LocalAI, Chroma, palace data paths, `.agents/plugins/marketplace.json`, or `docs/reference/`.
- Shared WP-08 API contract was set as `materialize_chatgpt_thread_embedding_cache(...)`, `build_embedding_source_text(...)`, and immutable `ChatGPTAtlasEmbeddingCacheResult`.

### 2026-05-11 - WP-08 Embedding Cache Evidence

- `O-0` reread this worksheet before worker acceptance review.
- `L-4` returned changed path: `mempalace/chatgpt_archive_atlas_embedding_cache.py`.
- `H-4` returned changed path: `tests/test_chatgpt_archive_atlas_embedding_cache.py`.
- `V-1` returned read-only acceptance guidance for exact thread embedding metadata fields, idempotency/partial-cache risks, static drift scan risks, and targeted acceptance commands.
- WP-08 delivered artifact-only `thread_embeddings.jsonl` and `thread_embedding_vectors.jsonl` materialization under a caller-supplied run directory, with injectable fake embedder support and real `mempalace.embedding` fallback for later live gates.
- WP-08 metadata rows are emitted through `contract.build_thread_embedding_metadata_row(...)` and record embedding id, model, effective device, vector dimensions, source text SHA-256, source text chars, batch index, status, and safety contract.
- WP-08 tests cover fake embedding materialization, metadata schema validation, effective device recording, vector dimensions, resume/idempotency, partial-cache resume, batch-size bounds, and deterministic source-text hash/embedding id behavior.
- `O-0` independently inspected the implementation, tests, and `V-1` acceptance guidance.
- `O-0` ran `.venv/bin/python -m pytest -q tests/test_chatgpt_archive_atlas_contract.py tests/test_chatgpt_archive_atlas_fixtures.py tests/test_chatgpt_archive_atlas_source.py tests/test_chatgpt_archive_atlas_runner.py tests/test_chatgpt_archive_atlas_conversation.py tests/test_chatgpt_archive_atlas_thread.py tests/test_chatgpt_archive_atlas_lexical_policy.py tests/test_chatgpt_archive_atlas_lexical_sketch.py tests/test_chatgpt_archive_atlas_embedding_cache.py`: `87 passed in 2.32s`.
- `O-0` ran `.venv/bin/python -m pytest -q tests/test_chatgpt_archive_atlas_contract.py -k "thread_embedding_metadata_row_contract_has_no_vector_payload_or_remote_fields or embedding_and_cluster_statuses_are_bounded"`: `2 passed, 24 deselected in 0.30s`.
- `O-0` ran `.venv/bin/python -m py_compile mempalace/chatgpt_archive_atlas_embedding_cache.py tests/test_chatgpt_archive_atlas_embedding_cache.py`: passed.
- `O-0` ran `.venv/bin/ruff check mempalace/chatgpt_archive_atlas_embedding_cache.py tests/test_chatgpt_archive_atlas_embedding_cache.py`: passed.
- `O-0` ran `git diff --check -- mempalace/chatgpt_archive_atlas_embedding_cache.py tests/test_chatgpt_archive_atlas_embedding_cache.py docs/worksheets/mempalace_chatgpt_archive_atlas_prellm_worksheet_2026-05-10.md`: passed.
- `O-0` statically scanned WP-08 code/tests for LocalAI, MCP, publish, drawer, palace write, Chroma, `/media/u0/Extreme SSD`, delete/remove surfaces, `requests`, `httpx`, and `openai`; matches were limited to the local variable name `requests` in the embedding cache implementation.
- WP-08 verdict: green.
- Checkpoint F verdict: green.
- Checkpoint F disposition: WP-09 is unlocked after this milestone is committed and pushed.

### 2026-05-11 - WP-09 Conservative Topic Clustering Activation

- `O-0` reread this worksheet before package activation.
- Current local branch truth before activation: `codex/mempalace-http-mcp-closure` at `8d9b7e7`.
- Current dirty files remain out of scope: modified `.agents/plugins/marketplace.json` and untracked `docs/reference/`.
- Activated WP-09 as the active semantic-lane package needed to close Checkpoint G.
- WP-09 lead `L-4` remains worker Banach with model `gpt-5.4` and reasoning depth `high`.
- WP-09 implementation write scope for `L-4` is limited to `mempalace/chatgpt_archive_atlas_topic_cluster.py`.
- WP-09 helper `H-4` remains worker Dirac with model `gpt-5.3-codex` and reasoning depth `medium`.
- WP-09 test write scope for `H-4` is limited to `tests/test_chatgpt_archive_atlas_topic_cluster.py`.
- WP-09 support `T-1` was assigned to worker Ohm with model `gpt-5.3-codex-spark` and reasoning depth `high` for read-only acceptance guidance.
- WP-09 workers were forbidden from editing docs, fixtures, runner, dashboard, MCP, LocalAI, Chroma, palace data paths, `.agents/plugins/marketplace.json`, or `docs/reference/`.
- Shared WP-09 API contract was set as `build_chatgpt_topic_cluster_rows(...)`, `build_chatgpt_topic_clusters(...)`, and immutable `ChatGPTAtlasTopicClusterResult`.

### 2026-05-11 - WP-09 Conservative Topic Clustering Evidence

- `O-0` reread this worksheet before worker acceptance review.
- `L-4` returned changed path: `mempalace/chatgpt_archive_atlas_topic_cluster.py`.
- `H-4` returned changed path: `tests/test_chatgpt_archive_atlas_topic_cluster.py`.
- `T-1` returned read-only acceptance guidance requiring conservative split invariants, candidate/mixed/noise cases, row contract checks, order independence, and no service/write surfaces.
- `O-0` rejected the first WP-09 return because vector-row validation required a `status` field not required by the accepted clustering input tests, and `warnings` were dicts instead of strings.
- `L-4` corrected vector input normalization and string warning output.
- WP-09 delivered deterministic conservative clustering from lexical rows plus vector rows, requiring both vector similarity and lexical overlap to merge, with candidate/mixed/noise statuses and stable cluster ids.
- WP-09 tests cover deterministic fake vectors, conservative non-merge cases, coherent candidate merge, noise handling, divergent evidence/no broad collapse, stable representative thread refs, and inspectable result summary fields.
- `O-0` independently inspected the implementation, tests, and `T-1` acceptance guidance.
- `O-0` ran `.venv/bin/python -m pytest -q tests/test_chatgpt_archive_atlas_contract.py tests/test_chatgpt_archive_atlas_fixtures.py tests/test_chatgpt_archive_atlas_source.py tests/test_chatgpt_archive_atlas_runner.py tests/test_chatgpt_archive_atlas_conversation.py tests/test_chatgpt_archive_atlas_thread.py tests/test_chatgpt_archive_atlas_lexical_policy.py tests/test_chatgpt_archive_atlas_lexical_sketch.py tests/test_chatgpt_archive_atlas_embedding_cache.py tests/test_chatgpt_archive_atlas_topic_cluster.py`: `95 passed in 2.57s`.
- `O-0` ran `.venv/bin/python -m pytest -q tests/test_chatgpt_archive_atlas_contract.py -k "topic_clusters_jsonl_row_contract or embedding_and_cluster_statuses_are_bounded"`: `2 passed, 24 deselected in 0.30s`.
- `O-0` ran `.venv/bin/python -m py_compile mempalace/chatgpt_archive_atlas_topic_cluster.py tests/test_chatgpt_archive_atlas_topic_cluster.py`: passed.
- `O-0` ran `.venv/bin/ruff check mempalace/chatgpt_archive_atlas_topic_cluster.py tests/test_chatgpt_archive_atlas_topic_cluster.py`: passed.
- `O-0` ran `git diff --check -- mempalace/chatgpt_archive_atlas_topic_cluster.py tests/test_chatgpt_archive_atlas_topic_cluster.py docs/worksheets/mempalace_chatgpt_archive_atlas_prellm_worksheet_2026-05-10.md`: passed.
- `O-0` statically scanned WP-09 code/tests for LocalAI, MCP, publish, drawer, palace write, Chroma, `/media/u0/Extreme SSD`, delete/remove surfaces, `requests`, `httpx`, `openai`, and subprocess: no matches.
- `O-0` ran an owner-side order-independence probe with shuffled lexical/vector rows: `order_independence_ok 2 [['thread-001', 'thread-002'], ['thread-003']]`.
- WP-09 verdict: green.
- Checkpoint G verdict: green.
- Checkpoint G disposition: WP-10 and WP-12 are unlocked after this milestone is committed and pushed.

### 2026-05-11 - WP-10 Markdown Atlas Summary Activation

- `O-0` reread this worksheet before package activation.
- Current local branch truth before activation: `codex/mempalace-http-mcp-closure` at `73ea3ba`.
- Current dirty files remain out of scope: modified `.agents/plugins/marketplace.json` and untracked `docs/reference/`.
- Activated WP-10 as the active report-lane package needed to close Checkpoint H.
- WP-10 lead `L-3` remains worker Euclid with model `gpt-5.4` and reasoning depth `high`.
- WP-10 implementation write scope for `L-3` is limited to `mempalace/chatgpt_archive_atlas_summary.py`.
- WP-10 docs/test helper `H-5` was assigned to worker Chandrasekhar with model `gpt-5.4-mini` and reasoning depth `medium`.
- WP-10 test write scope for `H-5` is limited to `tests/test_chatgpt_archive_atlas_summary.py`.
- WP-10 workers were forbidden from editing docs, fixtures, runner, dashboard, MCP, LocalAI, Chroma, palace data paths, `.agents/plugins/marketplace.json`, or `docs/reference/`.
- Shared WP-10 API contract was set as `build_chatgpt_atlas_summary(...)`, optional `write_chatgpt_atlas_summary(...)`, and immutable `ChatGPTAtlasSummaryResult`.

### 2026-05-11 - WP-10 Markdown Atlas Summary Evidence

- `O-0` reread this worksheet before worker acceptance review.
- `L-3` returned changed path: `mempalace/chatgpt_archive_atlas_summary.py`.
- `H-5` returned changed path: `tests/test_chatgpt_archive_atlas_summary.py`.
- WP-10 delivered deterministic Markdown atlas summary generation, manifest generation through `contract.build_atlas_summary_manifest(...)`, and a confined writer that writes only below the supplied run directory.
- WP-10 tests cover dataclass API shape, manifest validation, candidate wings/rooms, cluster sizes, evidence titles, top terms, representative excerpts, mixed/noisy clusters, source/error summaries, deterministic ordering, and writer confinement.
- `O-0` independently inspected the implementation and tests.
- `O-0` ran `.venv/bin/python -m pytest -q tests/test_chatgpt_archive_atlas_contract.py tests/test_chatgpt_archive_atlas_fixtures.py tests/test_chatgpt_archive_atlas_source.py tests/test_chatgpt_archive_atlas_runner.py tests/test_chatgpt_archive_atlas_conversation.py tests/test_chatgpt_archive_atlas_thread.py tests/test_chatgpt_archive_atlas_lexical_policy.py tests/test_chatgpt_archive_atlas_lexical_sketch.py tests/test_chatgpt_archive_atlas_embedding_cache.py tests/test_chatgpt_archive_atlas_topic_cluster.py tests/test_chatgpt_archive_atlas_summary.py`: `99 passed in 2.70s`.
- `O-0` ran `.venv/bin/python -m py_compile mempalace/chatgpt_archive_atlas_summary.py tests/test_chatgpt_archive_atlas_summary.py`: passed.
- `O-0` ran `.venv/bin/ruff check mempalace/chatgpt_archive_atlas_summary.py tests/test_chatgpt_archive_atlas_summary.py`: passed.
- `O-0` ran `git diff --check -- mempalace/chatgpt_archive_atlas_summary.py tests/test_chatgpt_archive_atlas_summary.py docs/worksheets/mempalace_chatgpt_archive_atlas_prellm_worksheet_2026-05-10.md`: passed.
- `O-0` statically scanned WP-10 code/tests for LocalAI, MCP, publish, drawer, palace write, Chroma, `/media/u0/Extreme SSD`, delete/remove surfaces, `requests`, `httpx`, `openai`, and subprocess: no matches.
- WP-10 verdict: green.
- Checkpoint H verdict: green.
- Checkpoint H disposition: WP-12 safety review is ready after this milestone is committed and pushed.

### 2026-05-11 - WP-12 Independent Safety Review Activation

- `O-0` reread this worksheet before package activation.
- Current local branch truth before activation: `codex/mempalace-http-mcp-closure` at `225e658`.
- Current dirty files remain out of scope: modified `.agents/plugins/marketplace.json` and untracked `docs/reference/`.
- Activated WP-12 as the independent review package needed to close Checkpoint I.
- WP-12 lead `R-1` was assigned to worker Darwin with model `gpt-5.5` and reasoning depth `high`.
- WP-12 is read-only: `R-1` has no write scope and was forbidden from editing files, committing, or pushing.
- WP-12 review scope includes all accepted atlas modules/tests plus the `snow-white-iii` systemd runner.

### 2026-05-11 - WP-12 Independent Safety Review Result

- `R-1` returned an explicit red verdict.
- Red finding 1: default embedding fallback can indirectly use Chroma's ONNX embedding implementation, which may perform `httpx` download, write under `~/.cache/chroma`, and remove a bad archive outside the atlas run directory.
- Red finding 2: `scripts/systemd/start_chatgpt_archive_atlas_snow_white_iii.sh` accepts an unvalidated `--run-id`, derives `RUN_DIR="$RUN_ROOT/$RUN_ID"`, and privileged-creates it; a path traversal run id could escape the run root.
- Amber finding 3: the transient unit grants `ReadWritePaths="$ROOT"` rather than the narrower atlas run boundary.
- Amber finding 4: the accepted branch lacks the Python atlas runner targeted by the systemd wrapper, so the live orchestration write surface is not reviewable.
- Positive checks: accepted atlas modules contain no direct LocalAI, OpenAI, HTTP client, MCP, palace publish, or Chroma collection-write calls; summary writer confines output under `run_dir`; embedding cache writes only its two JSONL artifacts under `run_dir` when using a safe injected embedder.
- WP-12 verdict: red.
- Checkpoint I remains blocked.
- Repair gate opened before WP-13: fix embedding backend safety, run-id/path confinement, systemd write boundary, and implement a reviewable Python atlas runner; then rerun independent `R-1` review.

### 2026-05-11 - WP-12 Repair Activation

- `O-0` reread the red `R-1` review before assigning repairs.
- Current local branch truth before repair activation: `codex/mempalace-http-mcp-closure` at `225e658`.
- Current dirty files remain out of scope: modified `.agents/plugins/marketplace.json` and untracked `docs/reference/`.
- Repair A: `L-4` worker Banach with model `gpt-5.4` and reasoning depth `high` was assigned to harden `mempalace/chatgpt_archive_atlas_embedding_cache.py` against implicit Chroma/httpx download/delete behavior.
- Repair A tests: `H-4` worker Dirac with model `gpt-5.3-codex` and reasoning depth `medium` was assigned to `tests/test_chatgpt_archive_atlas_embedding_cache.py`.
- Repair B: `L-5` worker Newton with model `gpt-5.3-codex` and reasoning depth `medium` was assigned to harden `scripts/systemd/start_chatgpt_archive_atlas_snow_white_iii.sh` and implement `mempalace/chatgpt_archive_atlas_runner.py`.
- Repair B tests: `V-1` worker Mencius with model `gpt-5.3-codex-spark` and reasoning depth `high` was assigned to `tests/test_chatgpt_archive_atlas_runner.py` and optionally `tests/test_chatgpt_archive_atlas_runner_cli.py`.
- Repair workers were forbidden from editing docs, fixtures, dashboard, MCP, LocalAI, Chroma, palace data paths, `.agents/plugins/marketplace.json`, or `docs/reference/`.

### 2026-05-11 - WP-12 Repair Evidence Before Re-Review

- `O-0` reread this worksheet before worker acceptance review.
- Repair A `L-4` returned changed path: `mempalace/chatgpt_archive_atlas_embedding_cache.py`.
- Repair A `H-4` returned changed path: `tests/test_chatgpt_archive_atlas_embedding_cache.py`.
- Repair A added a fail-closed guard before default Chroma ONNX embedding construction: the runner accepts real default embeddings only when the local `all-MiniLM-L6-v2` ONNX cache is already present under `~/.cache/chroma/onnx_models/all-MiniLM-L6-v2/onnx`; otherwise it raises before calling `mempalace.embedding.get_embedding_function(...)`.
- Injected embedding functions remain supported and bypass the default resolver for tests and future controlled callers.
- Repair B `L-5` returned changed paths: `scripts/systemd/start_chatgpt_archive_atlas_snow_white_iii.sh` and `mempalace/chatgpt_archive_atlas_runner.py`.
- Repair B `V-1` returned changed path: `tests/test_chatgpt_archive_atlas_runner.py`.
- Repair B validates `RUN_ID` before deriving `RUN_DIR`, rejects path separators and traversal slugs, resolves `RUN_ROOT`/`RUN_DIR`, enforces containment, keeps `/media/u0/Extreme SSD` refusal, and narrows transient `ReadWritePaths` to `$RUN_ROOT`.
- Repair B added the reviewable Python atlas runner and then an addendum repair for the worksheet progress rule: phase artifacts are materialized progressively, `progress.json` is updated after each phase and on failure, and runner no longer rewrites embedding JSONL artifacts owned by the embedding cache.
- `O-0` ran `.venv/bin/python -m pytest -q tests/test_chatgpt_archive_atlas_runner.py tests/test_chatgpt_archive_atlas_embedding_cache.py`: `21 passed in 1.14s`.
- `O-0` ran `.venv/bin/python -m pytest -q tests/test_chatgpt_archive_atlas_contract.py tests/test_chatgpt_archive_atlas_fixtures.py tests/test_chatgpt_archive_atlas_source.py tests/test_chatgpt_archive_atlas_runner.py tests/test_chatgpt_archive_atlas_conversation.py tests/test_chatgpt_archive_atlas_thread.py tests/test_chatgpt_archive_atlas_lexical_policy.py tests/test_chatgpt_archive_atlas_lexical_sketch.py tests/test_chatgpt_archive_atlas_embedding_cache.py tests/test_chatgpt_archive_atlas_topic_cluster.py tests/test_chatgpt_archive_atlas_summary.py`: `110 passed in 3.26s`.
- `O-0` ran `.venv/bin/python -m py_compile mempalace/chatgpt_archive_atlas_embedding_cache.py mempalace/chatgpt_archive_atlas_runner.py tests/test_chatgpt_archive_atlas_embedding_cache.py tests/test_chatgpt_archive_atlas_runner.py`: passed.
- `O-0` ran `.venv/bin/python -m ruff check mempalace/chatgpt_archive_atlas_embedding_cache.py mempalace/chatgpt_archive_atlas_runner.py tests/test_chatgpt_archive_atlas_embedding_cache.py tests/test_chatgpt_archive_atlas_runner.py`: passed.
- `O-0` ran `bash -n scripts/systemd/start_chatgpt_archive_atlas_snow_white_iii.sh`: passed.
- `O-0` ran `git diff --check`: passed.
- `O-0` statically scanned atlas modules/scripts/tests for LocalAI, MCP, publish, drawer, palace write, HTTP client, delete/remove, `/media/u0/Extreme SSD`, and broad `ReadWritePaths="$ROOT"` surfaces; matches were limited to forbidden-key contract/tests, synthetic lexical test strings, run-dir-local writer helpers, wrapper refusal text, and the local Chroma ONNX cache guard.
- `R-1` Darwin was sent the repaired surface for independent read-only re-review.
- `R-1` returned an explicit green verdict.
- `R-1` confirmed all four prior red/amber findings are repaired: default embedding is fail-closed before Chroma ONNX construction unless the local model cache is pre-warmed; systemd run id/path traversal is guarded; `ReadWritePaths` is narrowed to `$RUN_ROOT`; and the Python atlas runner is present and reviewable.
- `R-1` independently found no direct LocalAI, OpenAI/cloud HTTP client, MCP, publish, palace-write, Chroma collection write, or deletion API paths in the repaired runner or atlas modules.
- `R-1` independently ran `pytest -q tests/test_chatgpt_archive_atlas_runner.py tests/test_chatgpt_archive_atlas_embedding_cache.py`: `21 passed`.
- `R-1` independently ran py_compile, `bash -n`, and `git diff --check`: passed.
- WP-12 verdict: green.
- Checkpoint I verdict: green.
- Checkpoint I disposition: WP-13 bounded remote smoke is unlocked after this milestone is committed and pushed.

### 2026-05-11 - Checkpoint I Milestone Commit

- `O-0` staged only accepted WP-12 repair files: `docs/worksheets/mempalace_chatgpt_archive_atlas_prellm_worksheet_2026-05-10.md`, `mempalace/chatgpt_archive_atlas_embedding_cache.py`, `mempalace/chatgpt_archive_atlas_runner.py`, `scripts/systemd/README.md`, `scripts/systemd/start_chatgpt_archive_atlas_snow_white_iii.sh`, `tests/test_chatgpt_archive_atlas_embedding_cache.py`, and `tests/test_chatgpt_archive_atlas_runner.py`.
- Out-of-scope dirty files remained unstaged: modified `.agents/plugins/marketplace.json` and untracked `docs/reference/`.
- `O-0` ran `git diff --cached --check`: passed.
- `git commit -m "Resolve atlas safety review findings"` created `bff9f10`.
- `git push git@github.com:botman058/mempalace.git HEAD:refs/heads/codex/mempalace-http-mcp-closure` pushed `bff9f10` to the fork branch.

### 2026-05-11 - WP-13 Bounded Remote Smoke Activation

- `O-0` reread this worksheet before package activation.
- Current local branch truth before activation: `codex/mempalace-http-mcp-closure` at `bff9f10`.
- Current dirty files remain out of scope: modified `.agents/plugins/marketplace.json`, untracked `docs/reference/`, and this worksheet status update until its own status commit.
- Activated WP-13 as the live smoke package after Checkpoint I green.
- WP-13 lead remains `L-5`; live operations must run on `snow-white-iii`, as service user `mempalace`, with CPU cap `200%`, memory cap `16G`, and run artifacts under `/media/u0/OneDrive_Backup/mempalace/data/chatgpt_archive_atlas/<run_id>/`.
- WP-13 is bounded smoke only. No full archive run, LocalAI call, cloud LLM call, MCP publish, drawer mutation, palace write, deletion, service restart, or `/media/u0/Extreme SSD` path is allowed in WP-13.

### 2026-05-11 - WP-13 First Smoke Attempt Result

- `O-0` confirmed `u0@snow-white-iii` can stage under `/media/u0/OneDrive_Backup/tmp-mempalace` but cannot inspect/promote the live app tree and has no passwordless sudo.
- Direct `mempalace@snow-white-iii` remains unavailable because the service account has a nologin shell.
- Narrow root access was used only for app promotion and transient systemd control; the runner itself was launched through the wrapper as service user `mempalace`.
- A clean `git archive` of committed `HEAD` `51b77c1` was staged under `/media/u0/OneDrive_Backup/tmp-mempalace/codex-mempalace-app-20260512T034245Z-51b77c1/app` on `snow-white-iii`.
- Staged wrapper verification passed: `bash -n` for the atlas runner wrapper and promotion wrapper; `mempalace/chatgpt_archive_atlas_runner.py` existed in the staged tree.
- The staged app was promoted with `promote_snow_white_iii_app_update.sh`; promotion reported no file deletion, no service restart, and no palace data touch.
- Live compile check as `mempalace` passed for `mempalace/chatgpt_archive_atlas_runner.py` and `mempalace/chatgpt_archive_atlas_embedding_cache.py`.
- Local ONNX cache check as `mempalace` found the required `all-MiniLM-L6-v2` files under `/media/u0/OneDrive_Backup/mempalace/.cache/chroma/onnx_models/all-MiniLM-L6-v2/onnx`.
- Active service check before smoke showed only `mempalace-dashboard.service` and `mempalace-http.service`.
- Bounded smoke unit `mempalace-chatgpt-archive-atlas-atlas_smoke_20260512T0345Z_51b77c1` was submitted with `--limit 25`.
- The first smoke failed before artifact materialization. Journal evidence: `ImportError: attempted relative import with no known parent package` from direct file execution of `mempalace/chatgpt_archive_atlas_runner.py`.
- The failed attempt created only an empty diagnostic run directory under `/media/u0/OneDrive_Backup/mempalace/data/chatgpt_archive_atlas/atlas_smoke_20260512T0345Z_51b77c1`; no files were deleted and no palace data was touched.
- `python -m mempalace.chatgpt_archive_atlas_runner --help` worked as `mempalace` with `PYTHONPATH=/media/u0/OneDrive_Backup/mempalace/app`.
- WP-13 verdict: red for first smoke attempt; repair assigned before retry.
- Repair C: `L-5` Newton was assigned to make the wrapper invoke the runner package-safely.
- Repair C tests: `V-1` Mencius was assigned to add wrapper command coverage proving package-safe module invocation.

### 2026-05-11 - WP-13 Repair C Evidence

- `L-5` returned changed path: `scripts/systemd/start_chatgpt_archive_atlas_snow_white_iii.sh`.
- `V-1` returned changed path: `tests/test_chatgpt_archive_atlas_runner.py`.
- Repair C changed the transient unit command from direct file execution to package-safe module invocation with `python -m mempalace.chatgpt_archive_atlas_runner`.
- Repair C retained existing script existence checks, run-id/path guards, `ReadWritePaths="$RUN_ROOT"`, service user `mempalace`, `CPUQuota=200%`, `MemoryMax=16G`, and no LocalAI/MCP/publish surface.
- `O-0` ran `.venv/bin/python -m pytest -q tests/test_chatgpt_archive_atlas_runner.py tests/test_chatgpt_archive_atlas_embedding_cache.py`: `22 passed in 1.12s`.
- `O-0` ran `.venv/bin/python -m pytest -q tests/test_chatgpt_archive_atlas_contract.py tests/test_chatgpt_archive_atlas_fixtures.py tests/test_chatgpt_archive_atlas_source.py tests/test_chatgpt_archive_atlas_runner.py tests/test_chatgpt_archive_atlas_conversation.py tests/test_chatgpt_archive_atlas_thread.py tests/test_chatgpt_archive_atlas_lexical_policy.py tests/test_chatgpt_archive_atlas_lexical_sketch.py tests/test_chatgpt_archive_atlas_embedding_cache.py tests/test_chatgpt_archive_atlas_topic_cluster.py tests/test_chatgpt_archive_atlas_summary.py`: `111 passed in 3.23s`.
- `O-0` ran `bash -n scripts/systemd/start_chatgpt_archive_atlas_snow_white_iii.sh`: passed.
- `O-0` ran `.venv/bin/python -m py_compile tests/test_chatgpt_archive_atlas_runner.py`: passed.
- `O-0` ran `.venv/bin/python -m ruff check tests/test_chatgpt_archive_atlas_runner.py`: passed.
- `O-0` ran `git diff --check`: passed.
- Repair C verdict: green.
