# Session Memory (Phase 1)

Phase 1 keeps all per-run state in **session memory only**. Nothing is
persisted to disk or to a database. When the process exits, the session
ends and its contents are discarded.

## 1. What is a session?

A session is one execution of the `firm_short_workflow` for a single
input `instruction_id`. It is created when `run_workflow(...)` (or its
local fallback `run_workflow_local(...)`) is called, and it is destroyed
when the calling process exits.

## 2. Session-state schema

The `SessionState` Pydantic model in
`src/settlement_agent/domain/models.py` is the authoritative shape. It
mirrors what an ADK `Session` will carry in Phase 2.

| Field | Type | Written by |
|---|---|---|
| `run_id` | str (UUID-based) | workflow runner |
| `use_case_id` | str | workflow runner (from `use_cases/uc01_firm_short.yaml`) |
| `workflow_version` | str | workflow runner (from `firm_short_workflow.yaml`) |
| `instruction_id` | str | workflow input |
| `classification` | `ScenarioClassification` | Intake Agent |
| `evidence` | `EvidenceBundle` | Evidence Agent |
| `diagnosis` | `DiagnosisResult` | Diagnosis Agent |
| `commentary` | `CommentaryDraft` | Commentary Agent |
| `policy` | `PolicyResult` | Policy / HITL Agent |
| `approval` | `HumanApproval` | Human reviewer |
| `extras` | dict | reserved for ad-hoc keys |

## 3. `run_id`

`run_id` is `run-<12-hex>` generated via `uuid.uuid4().hex[:12]`. It is
unique per workflow invocation and serves as the session key.

## 4. Evidence captured per session

The `EvidenceBundle` stores:

- raw `ToolCallResult` envelopes for every tool invocation (tool name,
  input payload, returned records, timestamp, optional error)
- typed `PositionEvidence`, `SettlementEvidence`, `ReferenceEvidence`,
  and `TradeNettingEvidence` records

Every numeric or status claim that the Commentary Agent makes is
grounded in evidence rows held in this bundle.

## 5. What is NOT persisted in Phase 1

- No database writes.
- No file writes (except optional notebook output and pytest cache).
- No vector embeddings.
- No durable run state.
- No production audit log.
- No QMA messages — QMA send is deferred and human-controlled.

## 6. ADK integration notes

`run_workflow(...)` first tries to instantiate
`google.adk.sessions.InMemorySessionService` and stores a mirror of
`SessionState` under the ADK session's `state` dict. If ADK is not
installed or fails to initialise, the local fallback path is used
without losing any session-state fidelity.

## 7. Phase 2 direction

- **Durable run state**: persist `SessionState` snapshots to a key-value
  store (Redis / DynamoDB / Postgres) so runs survive process restarts.
- **RAG / pgvector**: add a vector store for SOPs, policies, and past
  case write-ups. Embed evidence summaries so the Diagnosis Agent can
  retrieve precedent cases.
- **Case memory**: replace `experience.md` with a structured KV store
  keyed by `case_id`.

## 8. Phase 3 considerations

- Encrypted at-rest run state with retention rules.
- Audit-replay tooling: rebuild any past commentary draft from stored
  evidence and prompts.
- Tenant-scoped session services for multi-desk operations.
