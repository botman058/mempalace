# MemPalace ChatGPT Overlap Dedupe - Orchestrated Worksheet
Date: 2026-05-04
Repo baseline: `/home/u4/repos/mempalace`
Live branch baseline: `codex/mempalace-http-mcp-closure` at `6e79485`
Observed branch relation: fork branch pushed through `6e79485`; `.agents/plugins/marketplace.json` is pre-existing/out of scope
Document type: implementation worksheet
Objective: make future overlapping ChatGPT privacy-export imports idempotent by stable per-conversation identity, without rewriting or deleting the current 135k raw drawers.

---

## control plane

### Top-level orchestrator

- **Only top-level orchestrator:** `O-0`
- **Model:** current Codex parent model
- **Reasoning depth:** high
- **Authority:** assign packages, enforce scope, review evidence, integrate accepted patches, update worksheet/devlog, push final branch
- **Forbidden uses:** direct package implementation, unannounced repo edits, deleting palace data, rewriting current raw corpus, touching `.agents/plugins/marketplace.json`
- **Mutation lock:** `O-0` is read/review/orchestrate-only by default.

### O-0 mutation lock

`O-0` is read/review/orchestrate-only until a package has explicit activation, bounded worker ownership, returned implementation evidence, required independent review, and an `O-0` checkpoint verdict.

Allowed mutation modes:

- `worksheet/status mode`: docs truth only.
- `integration mode`: reviewed worker-patch integration only.
- `emergency repair mode`: recorded bypass only.

Every mutation mode must be announced before the first write:

`Current gate: <mode>; allowed write scope: <paths>; reason: <checkpoint/package>.`

Any unannounced direct `O-0` code edit is red drift.

### Working rule

One worksheet controls the tranche: `docs/worksheets/mempalace_chatgpt_overlap_dedupe_worksheet_2026-05-04.md`.

`O-0` rereads the worksheet before package activation, worker acceptance, checkpoint closure, and devlog/handoff updates.

---

## reasoning-depth matrix

| Model | Depth | Intended uses | Forbidden uses |
|---|---:|---|---|
| Current parent | high | O-0 orchestration, review, integration | direct implementation outside mutation mode |
| gpt-5.4 | high | identity/miner leads, review | unrelated refactors |
| gpt-5.4-mini | medium | focused tests, docs, LocalAI compatibility | architecture ownership |
| gpt-5.3-codex-spark | medium | narrow verification | broad changes |

---

## standing constraints

1. Do not delete palace data or current raw drawers.
2. Do not rewrite the current 135k path-keyed raw corpus.
3. Do not use `/media/u0/Extreme SSD`.
4. Preserve LocalAI-only classification.
5. Scope dedupe to ChatGPT privacy exports.
6. Preserve non-ChatGPT conversation mining behavior.
7. Do not stage or modify `.agents/plugins/marketplace.json`.

---

## preserved baseline

- Raw ChatGPT mine completed with 135,182 `chatgpt` drawers from 19 `conversations.json` files.
- Current raw drawers are path-keyed and grandfathered.
- `mine_convos()` currently uses `source_file + chunk_index` for raw drawer IDs.
- `scripts/localai_chatgpt_signals.py` already has conversation checkpointing.
- Branch head is `6e79485`.

---

## agent pool

| ID | Model | Depth | Role | Intended use | Forbidden use |
|---|---|---:|---|---|---|
| O-0 | current parent | high | Orchestrator/integrator | Assign, review, checkpoint, integrate | package implementation |
| A-1 | gpt-5.4 | high | Identity lead | shared key/hash helper | docs-only closure |
| A-2 | gpt-5.4 | high | Miner lead | raw ChatGPT logical-source path | LocalAI changes |
| A-3 | gpt-5.4 | high | Reviewer | deletion/idempotency review | implementation under review |
| B-1 | gpt-5.4-mini | medium | Test worker | focused regression tests | miner architecture |
| B-2 | gpt-5.4-mini | medium | LocalAI/docs worker | checkpoint compatibility/docs | raw miner rewrite |

---

## package overview

| Package | Lead | Purpose | Size | Blocked by? |
|---|---|---|---:|---|
| WP-00 | O-0 | Create worksheet and freeze baseline | S | none |
| WP-01 | A-1 | Add shared ChatGPT identity/hash helper | S | WP-00 |
| WP-02 | A-2 | Add ChatGPT per-conversation iterator | S | WP-01 |
| WP-03 | A-2 | Wire skip behavior for unchanged logical sources | S | WP-02 |
| WP-04 | A-2 | Wire replace behavior for changed logical sources | S | WP-03 |
| WP-05 | B-2 | Align LocalAI checkpoint keys | S | WP-01 |
| WP-06 | B-1 | Add raw miner dedupe tests | S | WP-04 |
| WP-07 | B-1 | Add LocalAI/non-ChatGPT compatibility tests | S | WP-05 |
| WP-08 | A-3 | Independent review and drift check | S | WP-06, WP-07 |
| WP-09 | O-0 | Integration, docs, commit, push | S | WP-08 |

---

## orchestration protocol

Workers own bounded packages. `O-0` assigns, reviews, accepts/rejects, records drift, and integrates only after evidence. `O-0` must not preempt worker implementation because a change appears obvious.

Acceptable evidence:

- targeted tests proving overlap skip and changed-conversation replacement
- regression tests proving non-ChatGPT mining remains path-based
- LocalAI checkpoint compatibility test
- `py_compile`, targeted `pytest`, `git diff --check`
- worksheet/devlog updated before final push

Insufficient evidence:

- worker summary alone
- rerunning same path only
- docs saying dedupe exists
- any cleanup of existing palace data

---

## checkpoints and gates

### Checkpoint A - Baseline Frozen

- **Required evidence:** worksheet exists; branch/head/status recorded; out-of-scope dirty file noted.
- **Disposition:** green unlocks WP-01.

### Checkpoint B - Identity Contract Green

- **Required evidence:** helper tests for ID, fallback digest, selected-content hash.
- **Disposition:** green unlocks WP-02 and WP-05.

### Checkpoint C - Logical Iteration Green

- **Required evidence:** ChatGPT `conversations.json` list is decomposed into independent logical sources; non-ChatGPT path flow untouched.
- **Disposition:** green unlocks WP-03.

### Checkpoint D - Overlap Skip Green

- **Required evidence:** same ChatGPT conversation ID in different export paths skips and does not grow raw drawer count.
- **Disposition:** green unlocks WP-04.

### Checkpoint E - Changed Conversation Replace Green

- **Required evidence:** same ID with changed selected transcript purges/rebuilds only that logical source; old content absent for that logical source.
- **Disposition:** green unlocks WP-06.

### Checkpoint F - Compatibility Green

- **Required evidence:** LocalAI legacy checkpoint rows honored; non-ChatGPT mining remains path-based.
- **Disposition:** green unlocks review.

### Checkpoint G - Release Green

- **Required evidence:** targeted tests pass; docs updated; `.agents/plugins/marketplace.json` unstaged; commit pushed.
- **Disposition:** tranche closed.

---

## detailed work packages

### WP-00 - Worksheet and Baseline Freeze

- **owner:** `O-0`
- **lead:** `O-0`
- **support:** none
- **objective:** create the live worksheet and freeze branch/worktree truth.
- **why:** prevents drift into cleanup or direct O-0 implementation.
- **files/subsystems:** worksheet only.
- **deliverables:** live worksheet with branch/head/status.
- **acceptance:** Checkpoint A green.
- **exit:** WP-01 activation.

### WP-01 - Shared ChatGPT Identity Contract

- **owner:** `O-0`
- **lead:** `A-1`
- **support:** `B-1`
- **objective:** create one shared helper for ChatGPT logical identity and selected transcript hash.
- **why:** raw miner and LocalAI must not invent separate keys.
- **files/subsystems:** ChatGPT normalization/helper subsystem.
- **deliverables:** helper returns logical source ID, conversation ID metadata, selected transcript, source hash.
- **acceptance:** Checkpoint B green.
- **exit:** WP-02 and WP-05 activation.

### WP-02 - ChatGPT Logical Conversation Iterator

- **owner:** `O-0`
- **lead:** `A-2`
- **support:** `A-1`
- **objective:** make raw miner iterate ChatGPT export lists as independent logical conversation records.
- **why:** dedupe requires conversation-level source boundaries before skip/replace logic.
- **files/subsystems:** `mempalace/convo_miner.py`
- **deliverables:** internal path that yields logical ChatGPT records with original export path preserved as metadata.
- **acceptance:** Checkpoint C green.
- **exit:** WP-03 activation.

### WP-03 - Unchanged Overlap Skip

- **owner:** `O-0`
- **lead:** `A-2`
- **support:** `B-1`
- **objective:** skip future imports when logical source ID and source hash already match.
- **why:** this is the core overlapping-export idempotency behavior.
- **files/subsystems:** mined-source check path for ChatGPT logical records.
- **deliverables:** unchanged overlapping export produces zero new raw drawers.
- **acceptance:** Checkpoint D green.
- **exit:** WP-04 activation.

### WP-04 - Changed Conversation Replacement

- **owner:** `O-0`
- **lead:** `A-2`
- **support:** `B-1`
- **objective:** replace logical ChatGPT drawers when same conversation ID has changed selected transcript hash.
- **why:** user selected "Replace canonical."
- **files/subsystems:** purge/rebuild path for one logical ChatGPT source.
- **deliverables:** changed logical source deletes only its prior logical drawers and files new chunks.
- **acceptance:** Checkpoint E green.
- **exit:** WP-06 activation.

### WP-05 - LocalAI Checkpoint Compatibility

- **owner:** `O-0`
- **lead:** `B-2`
- **support:** `A-1`
- **objective:** align LocalAI signal checkpointing with shared identity while honoring legacy checkpoint rows.
- **why:** current LocalAI pass must not be reclassified because key format changed.
- **files/subsystems:** `scripts/localai_chatgpt_signals.py`
- **deliverables:** new checkpoint key format; legacy `conversations.json:<id>` rows treated as seen.
- **acceptance:** Checkpoint F LocalAI portion green.
- **exit:** WP-07 activation.

### WP-06 - Raw Miner Dedupe Tests

- **owner:** `O-0`
- **lead:** `B-1`
- **support:** `A-2`
- **objective:** add tests for raw overlap skip and changed-content replace.
- **why:** skip/replace behavior is the high-risk contract.
- **files/subsystems:** `tests/test_convo_miner.py`
- **deliverables:** tests for same ID/different path, same ID/changed content, missing ID fallback.
- **acceptance:** Checkpoints D and E proven by targeted pytest.
- **exit:** WP-08 after WP-07.

### WP-07 - Compatibility Tests

- **owner:** `O-0`
- **lead:** `B-1`
- **support:** `B-2`
- **objective:** prove unchanged non-ChatGPT mining and LocalAI legacy checkpoint compatibility.
- **why:** dedupe must not alter generic conversation imports or current signal pass resumability.
- **files/subsystems:** tests for convo miner and LocalAI script.
- **deliverables:** path-based non-ChatGPT regression; LocalAI legacy checkpoint regression.
- **acceptance:** Checkpoint F green.
- **exit:** WP-08.

### WP-08 - Independent Review

- **owner:** `O-0`
- **lead:** `A-3`
- **support:** none
- **objective:** review deletion safety, idempotency, and scope control.
- **why:** purge/rebuild behavior can destroy data if keyed incorrectly.
- **files/subsystems:** full accepted diff.
- **deliverables:** review verdict with findings or explicit no-issue statement.
- **acceptance:** all high/medium findings resolved or recorded as deferred.
- **exit:** O-0 may enter integration mode.

### WP-09 - Integration, Docs, Commit, Push

- **owner:** `O-0`
- **lead:** `O-0`
- **support:** none
- **objective:** integrate accepted patches, update docs/devlog, verify, commit, and push.
- **why:** final branch truth must match implemented behavior.
- **files/subsystems:** accepted worker changes, worksheet, relevant docs.
- **deliverables:** final verification log, commit, push to `git@github.com:botman058/mempalace.git`.
- **acceptance:** Checkpoint G green.
- **exit:** tranche closed.

---

## assumptions

- Future-only dedupe is intentional; existing 135k raw drawers are grandfathered.
- Same ChatGPT conversation ID with changed selected transcript uses "newest canonical replaces prior logical source."
- ChatGPT privacy exports are the only dedupe target.
- No automatic cleanup or migration of existing palace data is allowed.
- Remote serving remains on `snow-white-iii`; LocalAI remains local to `snow-white-iii`.
- Fork remote target remains `git@github.com:botman058/mempalace.git`.

---

## evidence log

### 2026-05-04 - WP-00 Baseline

- `git status --short --branch` reported branch `codex/mempalace-http-mcp-closure` with only out-of-scope dirty `.agents/plugins/marketplace.json`.
- `git rev-parse --short HEAD` reported `6e79485`.
- `mempalace health` reported remote CUDA health and drawer count `135791`.
- `mempalace-localai-chatgpt-signals.service` was active on `snow-white-iii`; remote deployment is deferred until it is safe to update the running script.

### 2026-05-04 - WP-01 through WP-07 Implementation Evidence

- A-1 added `mempalace/chatgpt_identity.py` and `tests/test_chatgpt_identity.py`, providing `ChatGPTIdentityRecord`, selected-path transcript extraction, logical source IDs, and stable source hashes.
- A-2 updated `mempalace/convo_miner.py` so only `conversations.json` uses ChatGPT logical-source mining. New drawers store `source_file=chatgpt:<id-or-digest>`, `logical_source_id`, `source_format=chatgpt`, original `source_path`, optional conversation metadata, and `source_hash`.
- B-2 updated `scripts/localai_chatgpt_signals.py` to checkpoint future classifications by logical source ID while honoring legacy classified keys. `skipped_empty` legacy rows no longer block a later classifiable conversation.
- B-1 added tests for overlap skip, changed-conversation replacement, missing-ID fallback, grandfathered path-keyed drawers, `conversations.json` filename scoping, non-ChatGPT path behavior, and LocalAI legacy checkpoint compatibility.
- O-0 integration fixed the second-review low issue by keeping stored transcript text on the historical `_messages_to_transcript()` path while computing `source_hash` from the unspellchecked selected transcript.

### 2026-05-04 - WP-08 Review Evidence

- A-3 first review found two medium issues and one low issue: legacy `skipped_empty` checkpoints could suppress future classification, logical mining applied to any ChatGPT-shaped `.json`, and `source_hash` depended on spellcheck behavior.
- O-0 fixed all three findings and added regression coverage for each medium finding plus the grandfathered-data gap.
- A-3 second review reported no remaining issues for the six requested contracts. The only low residual risk was the stored-transcript spellcheck drift, which O-0 then fixed by separating stored transcript text from hash transcript text.

### 2026-05-04 - Verification Evidence

- `python3 -m py_compile mempalace/chatgpt_identity.py mempalace/convo_miner.py scripts/localai_chatgpt_signals.py tests/test_chatgpt_identity.py tests/test_convo_miner.py tests/test_localai_chatgpt_signals.py` passed locally.
- `git diff --check` passed locally.
- `python3 -m pytest tests/test_chatgpt_identity.py tests/test_localai_chatgpt_signals.py -q` could not run locally because `tests/conftest.py` imports `chromadb`, which is not installed on `black-hole-iii`.
- Isolated CPU-only remote smoke under `/media/u0/OneDrive_Backup/tmp-mempalace/mempalace-dedupe-test-20260503203631` passed on `snow-white-iii`, proving same-ID overlap skip, changed-ID replacement, no-ID mapping fallback, `conversations.json` filename scoping, grandfathered path-keyed drawer preservation, and LocalAI `skipped_empty` compatibility.
- Live remote production app was not overwritten because `mempalace-localai-chatgpt-signals.service` was still active.
