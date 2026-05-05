# ChatGPT Signal Ontology Artifact Contract

Date: 2026-05-05
Applies to: WP-01, Checkpoint B, WP-02/WP-04/WP-05/WP-13 follow-on work
Status: normative

## 1. Scope

This contract defines the durable run artifacts for ontology work under:

`/media/u0/OneDrive_Backup/mempalace/data/ontology/<run_id>/`

It covers:

- `progress.json`
- phase JSONL files such as `pass1_open.jsonl`
- `artifacts_index.json`
- `accepted_routes.jsonl`
- `unresolved.jsonl`
- routed copy metadata attached to semantic copies

It does not define ontology prompts, clustering, routing logic, dashboard UI, or copy execution code.

## 2. Global rules

1. `chatgpt_signals` drawers are read-only source evidence.
2. Artifact files must be inspectable during an active run.
3. `progress.json` is the canonical dashboard summary. The dashboard must not derive canonical counts by rescanning whole JSONL files.
4. JSONL files are append-only. Existing lines are never edited in place.
5. JSON files (`progress.json`, `artifacts_index.json`) are rewritten atomically as whole files.
6. All timestamps are UTC RFC 3339 strings ending in `Z`.
7. All persisted wing/room keys are lowercase slug-safe identifiers matching `^[a-z0-9_]+$`.
8. Schema evolution is additive within `schema_version: 1`.

Common required fields on every root JSON object and every JSONL line:

| Field | Type |
|---|---|
| `schema_name` | `string` |
| `schema_version` | `integer` |
| `run_id` | `string` |

`run_id` must be filesystem-safe and content-free. Recommended format:
`YYYYMMDDTHHMMSSZ_chatgpt_signal_ontology`

## 3. Status values

Run status values:

- `pending`
- `running`
- `completed`
- `failed`
- `interrupted`
- `cancelled`

Phase status values:

- `not_started`
- `running`
- `completed`
- `failed`
- `skipped`

Generic phase record status values:

- `ok`
- `skipped`
- `invalid_model_output`
- `error`

Accepted route status values:

- `accepted`

Unresolved route status values:

- `null_route`
- `low_confidence`
- `conflict`
- `candidate_gap`
- `invalid_model_output`
- `verification_reject`
- `error`

## 4. `progress.json`

Purpose: compact active-run summary for the dashboard.

Required fields:

| Field | Type |
|---|---|
| `schema_name` | `string`; must be `ontology.progress` |
| `schema_version` | `integer`; must be `1` |
| `run_id` | `string` |
| `run_kind` | `string`; `chatgpt_signal_ontology` |
| `source_wing` | `string`; `chatgpt_signals` |
| `status` | `string`; run status enum |
| `current_phase` | `string|null` |
| `current_phase_status` | `string`; phase status enum |
| `phase_order` | `array[string]` |
| `phase_attempts` | `object<string, integer>`; 1-based attempts, `0` for not started |
| `started_at` | `string` |
| `updated_at` | `string` |
| `ended_at` | `string|null` |
| `elapsed_seconds` | `integer` |
| `current_phase_progress` | `object` |
| `totals` | `object` |
| `last_record` | `object|null` |
| `warning_count` | `integer` |
| `error_count` | `integer` |

`current_phase_progress` fields:

| Field | Type |
|---|---|
| `unit` | `string`; `drawer`, `candidate`, `route`, or `copy` |
| `total` | `integer|null` |
| `processed` | `integer` |
| `accepted` | `integer` |
| `unresolved` | `integer` |
| `errors` | `integer` |

`totals` fields:

| Field | Type |
|---|---|
| `source_drawers_total` | `integer` |
| `source_drawers_processed` | `integer` |
| `routes_accepted` | `integer` |
| `routes_unresolved` | `integer` |
| `copies_materialized` | `integer` |
| `phase_records_written` | `integer` |

`last_record` fields:

| Field | Type |
|---|---|
| `phase` | `string` |
| `relative_path` | `string` |
| `sequence` | `integer` |
| `subject_id` | `string` |
| `recorded_at` | `string` |

Update semantics:

- Rewrite atomically after durable phase-file writes.
- `updated_at`, `elapsed_seconds`, and counters are monotonic.
- Legal lifecycle: `pending -> running -> completed|failed|interrupted|cancelled`.
- `ended_at` is required for terminal states and `null` otherwise.
- `progress.json` must not include drawer bodies, prompts, full model output, or large candidate arrays.

Example:

```json
{
  "schema_name": "ontology.progress",
  "schema_version": 1,
  "run_id": "20260505T143015Z_chatgpt_signal_ontology",
  "run_kind": "chatgpt_signal_ontology",
  "source_wing": "chatgpt_signals",
  "status": "running",
  "current_phase": "pass1_open",
  "current_phase_status": "running",
  "phase_order": ["pass1_open", "candidate_clusters", "canonical_candidates", "route_candidates", "route_pass2", "route_verify", "apply_copies"],
  "phase_attempts": {"pass1_open": 1, "candidate_clusters": 0, "canonical_candidates": 0, "route_candidates": 0, "route_pass2": 0, "route_verify": 0, "apply_copies": 0},
  "started_at": "2026-05-05T14:30:15Z",
  "updated_at": "2026-05-05T14:41:02Z",
  "ended_at": null,
  "elapsed_seconds": 647,
  "current_phase_progress": {"unit": "drawer", "total": 1200, "processed": 148, "accepted": 0, "unresolved": 3, "errors": 1},
  "totals": {"source_drawers_total": 1200, "source_drawers_processed": 148, "routes_accepted": 0, "routes_unresolved": 3, "copies_materialized": 0, "phase_records_written": 148},
  "last_record": {"phase": "pass1_open", "relative_path": "pass1_open.jsonl", "sequence": 148, "subject_id": "drawer_chatgpt_signals_general_9f2a5ef5a06c8bd0c9c1a8c1", "recorded_at": "2026-05-05T14:41:01Z"},
  "warning_count": 3,
  "error_count": 1
}
```

## 5. Phase JSONL: `<phase>.jsonl`

Purpose: one durable line per processed subject in a phase.

Required fields:

| Field | Type |
|---|---|
| `schema_name` | `string`; must be `ontology.phase_record` |
| `schema_version` | `integer`; must be `1` |
| `run_id` | `string` |
| `phase` | `string` |
| `sequence` | `integer`; strictly increasing within the file |
| `attempt` | `integer`; 1-based |
| `recorded_at` | `string` |
| `subject_type` | `string` |
| `subject_id` | `string` |
| `record_status` | `string`; generic phase record status enum |
| `source` | `object`; at minimum `wing`, `room`, `drawer_id` when subject is a drawer |
| `payload` | `object`; phase-specific compact result |

Append semantics:

- Append exactly one new line per durable phase outcome.
- Never rewrite or delete prior lines.
- Retries or reruns use a higher `attempt` and a new `sequence`.
- `sequence` is file-local, monotonic, and never reused.

Important phase payloads:

- `candidate_clusters` records group first-pass `wing:room` hypotheses and
  carry candidate IDs, centroids, source drawer refs, and bounded examples.
- `canonical_candidates` records name, describe, merge, or prune those candidate
  groups. Payload `action` is `keep`, `merge`, or `prune`; merge payloads must
  identify the target candidate by candidate ID/key while preserving wing
  context.
- `route_candidates` records attach up to five plausible canonical candidates
  to one source drawer before route-pass prompting. Payloads include ranked
  candidate IDs/keys, canonical wing/room, label/definition, score features,
  source candidate refs, and bounded source excerpts.
- `route_pass2` records store the model route decision for one source drawer.
  Payloads choose one shortlist candidate or a null route, preserve shortlist
  provenance, include route confidence and concise rationale when present, and
  record invalid model output durably instead of crashing.

Example:

```json
{"schema_name":"ontology.phase_record","schema_version":1,"run_id":"20260505T143015Z_chatgpt_signal_ontology","phase":"pass1_open","sequence":148,"attempt":1,"recorded_at":"2026-05-05T14:41:01Z","subject_type":"drawer","subject_id":"drawer_chatgpt_signals_general_9f2a5ef5a06c8bd0c9c1a8c1","record_status":"invalid_model_output","source":{"wing":"chatgpt_signals","room":"general","drawer_id":"drawer_chatgpt_signals_general_9f2a5ef5a06c8bd0c9c1a8c1"},"payload":{"error_code":"missing_room_key","raw_response_excerpt":"{\"wing\":\"life_admin\"}","retryable":true}}
```

## 6. `artifacts_index.json`

Purpose: stable artifact directory for dashboard discovery.

Top-level fields:

| Field | Type |
|---|---|
| `schema_name` | `string`; `ontology.artifact_index` |
| `schema_version` | `integer`; `1` |
| `run_id` | `string` |
| `updated_at` | `string` |
| `artifacts` | `array[object]` |

Each `artifacts[]` entry:

| Field | Type |
|---|---|
| `artifact_key` | `string` |
| `relative_path` | `string` |
| `schema_name` | `string` |
| `schema_version` | `integer` |
| `artifact_kind` | `string`; `summary`, `phase_records`, `decision_records`, or `metadata` |
| `phase` | `string|null` |
| `content_type` | `string`; `application/json` or `application/jsonl` |
| `append_only` | `boolean` |
| `records` | `integer` |
| `bytes` | `integer` |
| `status` | `string`; `active`, `complete`, or `failed` |
| `dashboard_safe` | `boolean` |
| `privacy_level` | `string`; `summary`, `bounded_excerpt`, or `restricted` |
| `updated_at` | `string` |

Update semantics:

- Rewrite atomically after artifact creation or material change.
- Include only published artifacts the dashboard may reason about.
- `records` and `bytes` are monotonic for append-only artifacts.

Example:

```json
{
  "schema_name": "ontology.artifact_index",
  "schema_version": 1,
  "run_id": "20260505T143015Z_chatgpt_signal_ontology",
  "updated_at": "2026-05-05T14:41:02Z",
  "artifacts": [
    {"artifact_key":"progress","relative_path":"progress.json","schema_name":"ontology.progress","schema_version":1,"artifact_kind":"summary","phase":null,"content_type":"application/json","append_only":false,"records":1,"bytes":1332,"status":"active","dashboard_safe":true,"privacy_level":"summary","updated_at":"2026-05-05T14:41:02Z"},
    {"artifact_key":"pass1_open","relative_path":"pass1_open.jsonl","schema_name":"ontology.phase_record","schema_version":1,"artifact_kind":"phase_records","phase":"pass1_open","content_type":"application/jsonl","append_only":true,"records":148,"bytes":48122,"status":"active","dashboard_safe":false,"privacy_level":"restricted","updated_at":"2026-05-05T14:41:01Z"}
  ]
}
```

## 7. `accepted_routes.jsonl`

Purpose: durable record of routes that passed local verification and are eligible for copy materialization.

Required fields:

| Field | Type |
|---|---|
| `schema_name` | `string`; `ontology.accepted_route` |
| `schema_version` | `integer`; `1` |
| `run_id` | `string` |
| `sequence` | `integer` |
| `recorded_at` | `string` |
| `route_status` | `string`; `accepted` |
| `route_iteration` | `integer` |
| `source_drawer_id` | `string` |
| `source_wing` | `string` |
| `source_room` | `string` |
| `candidate_id` | `string` |
| `canonical_wing` | `string` |
| `canonical_room` | `string` |
| `route_confidence` | `number|null` |
| `verification_confidence` | `number|null` |
| `copy_ready` | `boolean` |
| `route_record_ref` | `string` |
| `verification_record_ref` | `string` |
| `rationale_summary` | `string` |

Semantics:

- Append-only.
- One line per accepted routing decision per run and iteration.
- `copy_ready: true` means later apply work may materialize a semantic copy; it does not mean the copy already exists.

Example:

```json
{"schema_name":"ontology.accepted_route","schema_version":1,"run_id":"20260505T143015Z_chatgpt_signal_ontology","sequence":1,"recorded_at":"2026-05-05T15:12:44Z","route_status":"accepted","route_iteration":1,"source_drawer_id":"drawer_chatgpt_signals_general_3d7e47b0d88b3a6c22d4d7a9","source_wing":"chatgpt_signals","source_room":"general","candidate_id":"cand_life_admin__appointments_and_forms","canonical_wing":"life_admin","canonical_room":"appointments_and_forms","route_confidence":0.93,"verification_confidence":0.96,"copy_ready":true,"route_record_ref":"route_pass2.jsonl#54","verification_record_ref":"route_verify.jsonl#54","rationale_summary":"Verified against drawer text, candidate definition, and source room context."}
```

## 8. `unresolved.jsonl`

Purpose: append-only record of cases that need retry, reroute, or manual review.

Required fields:

| Field | Type |
|---|---|
| `schema_name` | `string`; `ontology.unresolved_route` |
| `schema_version` | `integer`; `1` |
| `run_id` | `string` |
| `sequence` | `integer` |
| `recorded_at` | `string` |
| `route_iteration` | `integer` |
| `source_drawer_id` | `string` |
| `source_wing` | `string` |
| `source_room` | `string` |
| `unresolved_status` | `string`; unresolved status enum |
| `candidate_ids` | `array[string]` |
| `reason_code` | `string` |
| `reason_detail` | `string` |
| `route_confidence` | `number|null` |
| `next_action` | `string`; `reroute`, `manual_review`, `drop`, or `retry_later` |
| `retryable` | `boolean` |
| `source_excerpt` | `string|null`; bounded excerpt only |

Semantics:

- Append as soon as a case becomes unresolved.
- Later acceptance does not rewrite the unresolved line; resolution is represented by later records elsewhere.
- `source_excerpt` is optional and must remain short enough for dashboard preview use.

Example:

```json
{"schema_name":"ontology.unresolved_route","schema_version":1,"run_id":"20260505T143015Z_chatgpt_signal_ontology","sequence":2,"recorded_at":"2026-05-05T15:13:12Z","route_iteration":2,"source_drawer_id":"drawer_chatgpt_signals_general_55c58f6c1b3db93da6f13344","source_wing":"chatgpt_signals","source_room":"general","unresolved_status":"conflict","candidate_ids":["cand_life_admin__appointments_and_forms","cand_work_admin__meeting_coordination"],"reason_code":"verifier_disagreed","reason_detail":"Route pass selected life_admin, verifier preferred work_admin with overlapping evidence.","route_confidence":0.58,"next_action":"manual_review","retryable":false,"source_excerpt":"The drawer mixes meeting scheduling with personal paperwork and lacks a dominant target."}
```

## 9. Routed copy metadata

Purpose: prove lineage on the semantic copy without mutating the source drawer.

Required metadata fields on each routed copy:

| Field | Type |
|---|---|
| `ontology_copy_id` | `string` |
| `ontology_run_id` | `string` |
| `ontology_schema_version` | `integer`; `1` |
| `ontology_route_status` | `string`; `accepted` |
| `ontology_route_iteration` | `integer` |
| `ontology_source_drawer_id` | `string` |
| `ontology_source_wing` | `string` |
| `ontology_source_room` | `string` |
| `ontology_candidate_id` | `string` |
| `ontology_canonical_wing` | `string` |
| `ontology_canonical_room` | `string` |
| `ontology_route_record_ref` | `string` |
| `ontology_materialized_at` | `string` |
| `ontology_content_sha256` | `string` |

Idempotency expectations:

- `ontology_copy_id` must be deterministic for the accepted route target and source drawer.
- Reapplying the same accepted route must be a no-op, not a duplicate semantic drawer.
- `ontology_content_sha256` must let apply code confirm content identity before writing.
- Routed copy metadata must never be written back onto the original `chatgpt_signals` drawer.

Example:

```json
{
  "ontology_copy_id": "drawer_life_admin_appointments_and_forms_4cc9bcdb5f516d042583df53",
  "ontology_run_id": "20260505T143015Z_chatgpt_signal_ontology",
  "ontology_schema_version": 1,
  "ontology_route_status": "accepted",
  "ontology_route_iteration": 1,
  "ontology_source_drawer_id": "drawer_chatgpt_signals_general_3d7e47b0d88b3a6c22d4d7a9",
  "ontology_source_wing": "chatgpt_signals",
  "ontology_source_room": "general",
  "ontology_candidate_id": "cand_life_admin__appointments_and_forms",
  "ontology_canonical_wing": "life_admin",
  "ontology_canonical_room": "appointments_and_forms",
  "ontology_route_record_ref": "accepted_routes.jsonl#1",
  "ontology_materialized_at": "2026-05-05T15:15:19Z",
  "ontology_content_sha256": "3f4fdbb42c3fa11a6dcc3b810f76d6a98a0a86834c1b096676842360518b7db1"
}
```

## 10. Dashboard read contract

The dashboard is read-only and must:

1. Read `progress.json` for run state and counters.
2. Read `artifacts_index.json` to discover artifact files and privacy class.
3. Show bounded previews only for artifacts marked `dashboard_safe: true`.
4. Avoid treating missing optional files as fatal while a run is active.
5. Never trigger ontology writes, retries, applies, LocalAI calls, or source rescans.

The dashboard must not:

- compute canonical totals by scanning entire JSONL artifacts on refresh
- display full source drawer bodies from restricted artifacts
- infer accepted copies without `accepted_routes.jsonl` or copy metadata evidence

## 11. Privacy and safety

1. `progress.json` and `artifacts_index.json` must not contain raw drawer bodies, prompts, secrets, or full model transcripts.
2. JSONL artifacts may contain bounded excerpts only where explicitly allowed.
3. `source_excerpt` in `unresolved.jsonl` is for preview/debugging and should be minimal.
4. Artifact metadata must support dashboard inspection without creating a new mutation path.
5. No artifact defined here authorizes cloud upload or remote apply.
