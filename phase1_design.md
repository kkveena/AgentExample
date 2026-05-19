# Phase 1 Design — Agentic Settlement Commentary Reference

Companion to [`README.md`](./README.md) and [`agents.md`](./agents.md). The
README explains *what* you can run; this document explains *why* the code is
shaped the way it is, what the contracts are, and which seams Phase 2 is
expected to extend.

---

## 1. Scope of this document

This is the engineering design for **Phase 1** as actually shipped on the
`claude/setup-adk-settlement-phase1-Z2fGp` branch. It covers:

- the five-plane platform model and Phase 1's place in it
- repository layout (clean-architecture mapping) and module responsibilities
- the data model that flows through the workflow
- the YAML-first Development Plane
- the CSV-backed tool layer and its REST / MCP migration path
- the ADK-style root + sub-agent topology
- session memory, policy / HITL, and the eval harness
- the seams Phase 2 will use

Anything *aspirational* lives in section 12 (Phase 2 hooks). Everything else
in this document reflects code that exists on this branch today.

---

## 2. Goals and non-goals

### Goals

1. Reference implementation of the **firm-short-on-free-inventory** settlement
   commentary use case.
2. **YAML-first Development Plane**: use cases, agents, workflows, prompts,
   tools, policies, and evals are declared in YAML.
3. **Google ADK** as the target runtime; ship a local deterministic fallback
   so the workflow runs end-to-end without an API key or ADK install.
4. **CSV-backed mock tools** with Pydantic contracts identical to what a
   Phase 2 REST/MCP tool will expose.
5. **Session memory only** in Phase 1; mirror into ADK
   `InMemorySessionService` when ADK is available.
6. **Human-in-the-loop** approval gate — commentary is never marked final
   without explicit approval.
7. **Eval harness from day one** — every Phase 1 scenario has an eval case.
8. Clean-architecture boundaries so Phase 2 can extend without rewrites.

### Non-goals (deferred to Phase 2+)

- MCP server implementation, REST-backed tool adapters
- pgvector / RAG memory, durable run-state storage
- Automatic QMA send (kept human-controlled)
- Production authn/authz, entitlement, audit dashboards
- Full User Plane / workflow builder

---

## 3. Platform model (five planes)

| Plane | Phase 1 treatment | Phase 2 direction |
|---|---|---|
| User Plane | not built | workflow builder for PMs / senior devs |
| Development Plane | **primary focus** — YAML + Python typed contracts | YAML validator, compiler, ADK workflow generator |
| Memory Plane | session memory only; `experience.md` as case-memory scratchpad | pgvector RAG, durable run state, structured case-memory KV |
| MCP Plane | deferred (tool contracts preserved) | MCP server fronting REST-backed tools |
| Control Plane | lightweight HITL approval, evals | policy registry, eval gates, observability, audit replay |

Phase 1 spends its effort on the Development Plane because that is where
business analysts and senior developers will live. The other planes have
preserved seams (tool contracts, session-state shape, policy YAML) but no
implementation.

---

## 4. Repository layout (clean architecture)

```
src/settlement_agent/
  config.py                       # runtime config + Phase 2 feature flags
  config/                         # YAML Development Plane
    use_cases/ agents/ workflows/ prompts/ tools/ policies/ evals/
  domain/                         # pure business concepts, no I/O
    models.py                     # Pydantic tool I/O + session state
    exceptions.py
    utils.py
    tools/                        # tool contracts + CSV-backed impls
    prompts/                      # prompt registry (YAML-backed)
    memory/                       # session + case-memory interfaces
  application/                    # use-case services
    chat_service/                 # ADK root + sub-agent enclosure
      root_agent.py
      workflow.py                 # thin entry point
      sub_agents/{intake,evidence,diagnosis,commentary,policy_hitl}_agent.py
    evaluation_service/eval_runner.py
    reset_memory_service/reset.py
    ingest_documents_service/     # Phase 2 RAG ingest placeholder
  infrastructure/                 # adapters to the outside world
    config_loader.py              # YAML loader
    api/                          # FastAPI surface (Phase 2)
    db/csv_loader.py              # Phase 1 CSV reader
    llm_providers/ mcp_clients/ monitoring/   # Phase 2 placeholders
```

### Layer rules

- **`domain/`** depends only on `pydantic` and `pyyaml`. No file I/O, no
  third-party SDKs, no HTTP. Anything reusable across services lives here.
- **`application/`** orchestrates `domain/` against `infrastructure/`.
  Each subdirectory is one use-case service.
- **`infrastructure/`** is the only place file system, HTTP, MCP, LLM, or DB
  access lives. Adapters are swappable; the rest of the package never
  imports a vendor SDK directly.
- **`config/`** (YAMLs) is the Development Plane and stays centralized so a
  developer can reason about the whole workflow declaration in one place.

### Cross-cutting principles

- Every tool boundary is a Pydantic model (deterministic, typed,
  serialisable).
- Every agent boundary writes into `SessionState` (mirror of ADK session
  state).
- No internal source-system names anywhere in code, prompts, or commentary.
- "Insufficient evidence" is always preferable to speculation.

---

## 5. Data model

All types live in `domain/models.py`. The model graph below is what flows
between sub-agents and into `SessionState`.

```
SessionState
├── run_id, use_case_id, workflow_version, instruction_id
├── classification : ScenarioClassification
├── evidence       : EvidenceBundle
│     ├── position[]      : PositionEvidence
│     ├── settlement[]    : SettlementEvidence
│     ├── reference[]     : ReferenceEvidence
│     ├── trade_netting[] : TradeNettingEvidence
│     └── tool_calls[]    : ToolCallResult   (raw tool envelopes)
├── diagnosis      : DiagnosisResult
├── commentary     : CommentaryDraft
├── policy         : PolicyResult
└── approval       : HumanApproval (pending | approved | rejected | needs_edit)
```

### Stability contract

`SessionState` and every nested model are **frozen contracts**. Phase 2 may
add optional fields (with defaults) or write into `SessionState.extras`,
but the existing shape will not change. This is what lets us swap
deterministic agents for LLM-backed ADK `LlmAgent`s without touching the
notebook, evals, or tests.

### Tool I/O

Each tool has an explicit `*Input` and `*Evidence` Pydantic model. The
generic `ToolCallResult` envelope is what the registry returns, and is the
exact shape an MCP tool call will return in Phase 2:

```python
class ToolCallResult(BaseModel):
    tool_name: str
    input_payload: dict
    records: list[dict]
    record_count: int
    source: str = "csv_mock"
    retrieved_at: datetime
    error: Optional[str]
```

---

## 6. YAML Development Plane

The `config/` tree is the canonical description of the workflow.

| File | Owns |
|---|---|
| `use_cases/uc01_firm_short.yaml` | Use case id, owner, inputs, outputs, Phase 1 out-of-scope list |
| `agents/agents.yaml` | The five logical agents and their inputs/outputs |
| `workflows/firm_short_workflow.yaml` | Sequential workflow steps + session-state schema |
| `prompts/prompts.yaml` | Prompt registry (each sub-agent references a `prompt_ref`) |
| `tools/tools.yaml` | Tool I/O contracts and Phase 1 vs future backend |
| `policies/policy.yaml` | HITL gates, forbidden tokens, allowed approval states |
| `evals/eval_cases.yaml` | Eval scenarios (input → expected reason / tools / approval) |

### Validation

`infrastructure/config_loader.py::validate_all_configs()` enforces required
top-level keys per file. Tests in `tests/unit/test_yaml_config.py` keep
this honest.

### Why YAML, why central

The intended Phase 2 reader of these files is a workflow builder and a
configuration compiler — both prefer a single tree to walk. Splitting YAMLs
across `domain/<thing>/` would scatter the Development Plane and make the
Phase 2 compiler harder to write.

---

## 7. Tool layer

Each Phase 1 tool is a thin function under `domain/tools/`:

```python
def call_position_tool(payload: PositionToolInput) -> ToolCallResult:
    rows = load_positions()                # infrastructure/db/csv_loader
    matches = filter_rows(rows, **payload) # tools/base.py
    return ToolCallResult(...)
```

The four tools are: `position_tool`, `settlement_tool`,
`reference_data_tool`, `trade_netting_tool`. They are registered in
`domain/tools/registry.py` so agents resolve them **by name** — exactly
how MCP toolsets will resolve tools in Phase 2.

### Migration path

```
CSV-backed Python function
   ↓  (same Pydantic contract)
REST-backed adapter (infrastructure/api + infrastructure/db)
   ↓  (registered in MCP server)
MCP server tool
   ↓  (consumed by ADK MCPToolset)
ADK sub-agent
```

Only `infrastructure/db/csv_loader.py` must change to migrate a tool. The
`domain/tools/*_tool.py` files and `tools.yaml` contracts stay put.

### What is *not* a tool in Phase 1

QMA draft / send is intentionally not a tool. Phase 1 wants QMA to remain
a human-controlled action; introducing it as a tool now would risk an
LLM-driven sub-agent eventually invoking it.

---

## 8. Agent topology

The ADK-style enclosure lives under `application/chat_service/`:

```
root_agent (SequentialAgent-style orchestrator)
  ├── intake_agent       → ScenarioClassification
  ├── evidence_agent     → EvidenceBundle (calls 4 tools)
  ├── diagnosis_agent    → DiagnosisResult (firm-short business rules)
  ├── commentary_agent   → CommentaryDraft (factual, evidence-grounded)
  └── policy_hitl_agent  → PolicyResult + routes to human approval
```

Each sub-agent module exposes two things:

1. **`run(...)`** — the deterministic Phase 1 implementation used by the
   workflow, tests, evals, and notebook.
2. **`build_adk_agent()`** — a factory that returns a Google ADK
   `LlmAgent` instance when `google-adk` is installed (returns `None`
   otherwise). Phase 2 fills in real prompts and tool bindings here.

`root_agent.build_root_agent()` composes the five factories into a
Google ADK `SequentialAgent`. When ADK is not installed, `root_agent.run()`
executes the deterministic chain.

### Why deterministic in Phase 1

- The workflow needs to be testable in CI without an LLM provider.
- The eval harness needs a stable baseline to compare LLM output against
  in Phase 2.
- The business rules (firm-short, encumbered, realignment, incoming
  cover, counterparty short, rejected, intercompany, netting mismatch)
  are explicit and reviewable in `diagnosis_agent.py`.

### Why one file per sub-agent

Phase 2 will replace the body of `run()` with an LLM call and grow the
`build_adk_agent()` factory to include real prompts and tool bindings.
Keeping each agent isolated keeps that change a one-file diff per agent.

---

## 9. Workflow execution

`application/chat_service/workflow.py` is a 30-line entry point:

```
run_workflow(instruction_id, approval_status?)
  → run_workflow_local(...)  → root_agent.run(...)
                                  → intake → evidence → diagnosis
                                  → commentary → policy
                                  → apply approval (if provided)
  → if ADK installed: mirror SessionState into InMemorySessionService
  → return SessionState
```

### Approval semantics

- Default: `approval.status = "pending"` and `is_final()` is `False`.
- Caller passes `approval_status="approved" | "rejected" | "needs_edit"`
  to record a decision; only `"approved"` makes `is_final()` true.
- Policy gate **always** requires human approval — the workflow cannot
  auto-finalise even if the policy result is clean.

### ADK fallback behaviour

If `google-adk` is missing or session creation fails, the workflow falls
back to the deterministic root agent silently. The returned
`SessionState` shape is identical in both paths, so tests and the
notebook are agnostic.

---

## 10. Session memory

See [`sessions.md`](./sessions.md) for the full spec. Key points:

- `SessionState` is the authoritative shape. `domain/memory/session.py`
  re-exports it so the import path is stable while the model definition
  stays co-located in `domain/models.py`.
- `run_id` is `run-<12-hex>` (uuid4-derived). Unique per workflow call.
- Nothing is persisted in Phase 1. The process exiting destroys the
  session.
- ADK mirroring is best-effort and never blocks the workflow.

`domain/memory/case_memory.py` defines a `CaseMemory` Protocol with `get`,
`put`, and `search`. No implementation in Phase 1; Phase 2 adds a KV
adapter and later a pgvector adapter behind this interface.

---

## 11. Policy and Human-in-the-Loop

`policy_hitl_agent.run(...)` runs **structural** checks, not semantic
ones:

- commentary has at least one evidence reference,
- commentary does not contain forbidden tokens (placeholders for internal
  system names),
- firm-short claims have at least one position-evidence record,
- the draft is not flagged as containing unsupported claims.

`PolicyResult.requires_human_approval` is **always `True`** in Phase 1.
This is a hard constraint: even a clean policy result is not enough to
finalise commentary.

`apply_human_approval(status, reviewer, comments)` is the function the
notebook / CLI / future UI calls to record a decision. Allowed states:
`pending`, `approved`, `rejected`, `needs_edit`.

---

## 12. Eval harness

`application/evaluation_service/eval_runner.py` is the Phase 1 eval driver.
For each YAML case it:

1. Runs `run_workflow_local(instruction_id, approval_status="approved")`.
2. Checks: scenario label, reason code, required tools called, evidence
   bundle exists, required evidence fields present, commentary has
   evidence references, commentary has no large numeric tokens without
   evidence backing, no auto-QMA-send, human approval required.
3. Returns an `EvalResult` per case.

Phase 1 ships with five cases (firm short confirmed, incoming receive
covers, insufficient evidence, counterparty short, netting mismatch).
All pass; CI fails if any regress.

The notebook section 9 demonstrates two developer views: the CLI-style
verbose trace and a per-case expansion with expected vs actual values.

---

## 13. Sequence (firm-short, happy path)

```
caller / notebook
   │
   ▼
run_workflow("SI-DLV-1001", approval_status="approved")
   │
   ▼ root_agent.run()
       intake_agent → SessionState.classification = ScenarioClassification(
                          scenario_label="firm_short", case_id="UC-01-FIRM-SHORT")
       evidence_agent
           settlement_tool({"instruction_id": "SI-DLV-1001"})  → 1 record
           position_tool({"account_id": "ACC-DLV-001",
                          "security_id": "SEC-US-0001"})       → 1 record
           reference_data_tool({"security_id": "SEC-US-0001"}) → 1 record
           trade_netting_tool({...})                           → 1 record
           ⇒ SessionState.evidence = EvidenceBundle(...)
       diagnosis_agent → SessionState.diagnosis = DiagnosisResult(
                              reason_code="FIRM_SHORT_FREE_INVENTORY",
                              is_firm_short=True, ...)
       commentary_agent → SessionState.commentary = CommentaryDraft(
                              text="Delivery remains pending for Alpha Corp ...",
                              evidence_refs=[...], grounded=True)
       policy_hitl_agent → SessionState.policy = PolicyResult(
                                passed=True,
                                requires_human_approval=True)
       apply_human_approval("approved", ...) → SessionState.approval
   │
   ▼
SessionState (is_final() == True)
```

---

## 14. Testing strategy

Three test tiers under `tests/`:

- `tests/unit/` — CSV loading, tool I/O, YAML config validation.
- `tests/integration/` — end-to-end workflow run and approval transitions.
- `tests/agent/` — eval runner over the YAML suite.

All Phase 1 tests run via `pytest` (24 tests) and `make eval` (5
scenarios). CI on every push to `claude/**` and `main` via
`.github/workflows/tests.yml`.

The notebook is executed end-to-end during local dev with `nbclient`; its
outputs are committed so GitHub renders them inline.

---

## 15. Phase 2 hooks (seams already in place)

These hooks exist on the branch today. Phase 2 work plugs into them
without restructuring.

| Hook | Where | Phase 2 use |
|---|---|---|
| `build_adk_agent()` on every sub-agent | `application/chat_service/sub_agents/*` | swap deterministic `run()` for a real `LlmAgent` |
| `build_root_agent()` | `application/chat_service/root_agent.py` | returns a `SequentialAgent(sub_agents=[...])` once factories return real `LlmAgent`s |
| `ToolCallResult` envelope | `domain/models.py` | identical shape an MCP tool returns |
| `domain/tools/registry.py` | name-based tool lookup | mirrors how MCP `Toolset` resolves tools |
| `domain/memory/case_memory.py::CaseMemory` Protocol | interface only | impl lands in `infrastructure/` later (KV → pgvector) |
| `infrastructure/llm_providers/` `mcp_clients/` `monitoring/` `api/` | empty packages | hold the Phase 2 adapters |
| `application/reset_memory_service/reset.py` | clears Phase 1 caches | extends to clear durable session + case stores |
| `application/ingest_documents_service/` | empty package | holds RAG ingest pipeline |
| `config.py` feature flags | `USE_LLM_AGENTS`, `TOOL_BACKEND`, `SESSION_STORE` | dual-path roll-outs |

The end-state of Phase 2 will not require any change to:

- the YAML configs under `config/`,
- the Pydantic models in `domain/models.py`,
- the `SessionState` shape,
- the tool registry interface,
- the notebook (other than swapping to an LLM-backed run).

---

## 16. Known limitations

- Agents are deterministic Python. The LLM path is wired but not yet
  invoked from the workflow (Phase 2 M1).
- `commentary_no_unsupported_numbers` is a regex heuristic, not a
  factuality model. Good enough for Phase 1; replace with an
  LLM-as-judge eval in Phase 2 M9.
- No persistent storage. Process exit drops session state. Phase 2 M5
  addresses this.
- No real LLM provider integration; `infrastructure/llm_providers/` is
  empty.
- ADK mirroring uses an in-memory session service; no remote ADK runner.
- `experience.md` is markdown, not a queryable store.

---

## 17. Open design questions

These are flagged here rather than decided.

1. **Workflow versioning.** `workflow_version` is captured per run but
   not yet wired into the eval harness; should evals key on
   `(use_case_id, workflow_version)`?
2. **Reason-code taxonomy.** The current code maps reason codes 1:1 with
   the scenario manifest. As scenarios multiply, do we promote reason
   codes to a YAML registry under `config/`?
3. **Policy severity vs hardness.** `policy.yaml` has a `severity: hard`
   field but Phase 1 treats every constraint as blocking. Phase 2 should
   honour `severity: soft` for warnings.
4. **Forbidden-tokens list.** Currently lives in
   `policy_hitl_agent.py::FORBIDDEN_TOKENS`. Should move into
   `policy.yaml` once Phase 2 needs more than three entries.
5. **Notebook as test artifact.** Should the executed notebook be
   re-rendered by CI to detect output drift, or only by local dev?

---

## 18. References

- [`README.md`](./README.md) — install / run instructions, high-level
  overview, acceptance criteria.
- [`agents.md`](./agents.md) — guidance for AI coding agents working in
  this repo.
- [`SKILLS.md`](./SKILLS.md) — how to add tools, workflows, evals.
- [`sessions.md`](./sessions.md) — session memory specification.
- [`experience.md`](./experience.md) — temporary case memory examples.
- [`data/README.md`](./data/README.md) — sample CSV schema, join keys,
  REST/MCP migration plan.
