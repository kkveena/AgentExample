# Agentic Settlement Commentary Platform

Phase 1 reference implementation for an agentic settlement commentary workflow using **Google ADK** as the runtime and a **YAML-first Development Plane**.

## 1. Purpose

This project implements the reference use case:

> **Firm is short on free inventory for delivery.**

In settlement operations, analysts investigate pending delivery obligations by gathering evidence from position, settlement, reference data, and trade/netting sources. They then prepare factual commentary for QMA, the operations email interaction channel used by humans to communicate with counterparties.

This implementation does **not** automatically send QMA messages. The system collects evidence, diagnoses the scenario, drafts factual commentary, and routes the draft to a human reviewer.

## 2. Phase 1 Scope

Phase 1 focuses on the **Development Plane**.

### In scope

- YAML-first configuration for use cases, agents, workflows, tools, prompts, policies, and evals
- Google ADK-oriented runtime design
- CSV-backed mock tools
- Session memory only
- `experience.md` as temporary case memory
- Human-in-the-loop review / approval
- Jupyter notebook for end-to-end testing
- Pytest test suite
- Evals from day one
- Data dictionary-driven implementation

### Out of scope for Phase 1

- MCP server implementation
- REST API-backed production tools
- pgvector / RAG memory
- Automatic QMA sending
- Production authentication / entitlementing
- Full UI / User Plane
- Persistent run-state database

## 3. Platform Plan

The long-term platform has five planes:

| Plane | Phase 1 Treatment | Future Direction |
|---|---|---|
| User Plane | Not built in Phase 1 | Workflow builder for PMs / senior developers |
| Development Plane | Primary focus | YAML validation, compiler, ADK workflow generation |
| Memory Plane | Session memory only | pgvector RAG, durable run state, case memory store |
| MCP Plane | Deferred | MCP tools backed by REST APIs |
| Control Plane | Lightweight HITL approval | Policy registry, eval gates, observability, audit replay |

## 4. Reference Workflow

The Phase 1 workflow should model the following agent sequence:

```text
User / instruction input
   ↓
Intake Agent
   ↓
Evidence Agent
   ↓
Diagnosis Agent
   ↓
Commentary Agent
   ↓
Policy / Human-in-the-loop Agent
   ↓
Approved / rejected / needs edit
```

### Agent responsibilities

| Agent | Responsibility |
|---|---|
| Intake Agent | Classify scenario and extract instruction context |
| Evidence Agent | Call CSV-backed tools and build evidence bundle |
| Diagnosis Agent | Apply firm-short business rules |
| Commentary Agent | Draft factual commentary grounded in evidence |
| Policy / HITL Agent | Validate facts, check constraints, route for approval |

## 5. CSV-Backed Tools

Phase 1 tools read from CSV files under `data/`. These are mock tool implementations that will later be replaced by MCP/REST-backed tools.

| Tool | CSV Source | Purpose |
|---|---|---|
| Position Tool | `data/position_data.csv` | Free, pledged, segregated, and total position evidence |
| Settlement Tool | `data/settlement_data.csv` | Delivery/receive instruction and settlement status evidence |
| Reference Data Tool | `data/reference_data.csv` | Security, account, counterparty, and location reference facts |
| Trade / Netting Tool | `data/trade_netting_data.csv` | Gross/net trade quantities and receive coverage evidence |

Important: `data/data_dictionary.csv` is the authoritative reference for field names, field definitions, and expected usage.

## 6. Data Directory Requirements

The `data/` directory should include:

```text
data/
  README.md
  data_dictionary.csv
  position_data.csv
  settlement_data.csv
  reference_data.csv
  trade_netting_data.csv
  scenario_manifest.csv
```

`data/README.md` must explain:

- what each CSV contains
- which tool uses each file
- join keys across files
- synthetic data assumptions
- how to use `data_dictionary.csv`
- how CSV tools will later become REST/MCP-backed tools

## 7. Repository Structure

The Phase 1 package is named `settlement_agent`.

```text
.github/
notebook/
  phase1_firm_short_reference_workflow.ipynb
data/
  README.md
  data_dictionary.csv
  position_data.csv
  settlement_data.csv
  reference_data.csv
  trade_netting_data.csv
  scenario_manifest.csv
src/settlement_agent/
  __init__.py
  config.py                       # runtime config + Phase 2 feature flags
  config/                         # YAML Development Plane
    use_cases/ agents/ workflows/ prompts/ tools/ policies/ evals/
  domain/                         # pure business concepts (no I/O)
    models.py                     # Pydantic tool I/O + session state
    exceptions.py
    utils.py
    tools/                        # tool contracts + CSV-backed impls
      base.py
      position_tool.py settlement_tool.py
      reference_data_tool.py trade_netting_tool.py
      registry.py
    prompts/                      # prompt registry (YAML-backed)
    memory/                       # session + case-memory interfaces
      session.py case_memory.py
  application/                    # use-case services
    chat_service/                 # ADK-style root + sub-agent enclosure
      root_agent.py
      workflow.py                 # thin entry point
      sub_agents/
        intake_agent.py evidence_agent.py
        diagnosis_agent.py commentary_agent.py
        policy_hitl_agent.py
    evaluation_service/
      eval_runner.py
    reset_memory_service/
      reset.py
    ingest_documents_service/     # Phase 2 RAG ingest placeholder
  infrastructure/                 # adapters to the outside world
    config_loader.py              # YAML loader
    api/                          # FastAPI surface (Phase 2)
    db/
      csv_loader.py               # Phase 1 CSV reader
    llm_providers/                # Anthropic / Vertex / OpenAI (Phase 2)
    mcp_clients/                  # MCP server + ADK MCPToolset (Phase 2)
    monitoring/                   # structured logging / traces (Phase 2)
tests/
  unit/
  integration/
  agent/
Makefile
pyproject.toml
README.md
agents.md
SKILLS.md
sessions.md
experience.md
```

## 8. YAML-First Development Plane

The workflow should be configured through YAML files rather than hard-coded in the notebook.

Suggested configuration areas:

```text
src/<package_name>/config/use_cases/
src/<package_name>/config/agents/
src/<package_name>/config/workflows/
src/<package_name>/config/prompts/
src/<package_name>/config/tools/
src/<package_name>/config/policies/
src/<package_name>/config/evals/
```

The YAML definitions should cover:

- use case metadata
- agent roles
- workflow sequence
- tool bindings
- prompt references
- memory requirements
- policy gates
- eval cases

## 9. Memory Design for Phase 1

Phase 1 memory is session-only.

Create `sessions.md` to document what is stored during the workflow.

Session memory should include:

- `run_id`
- `use_case_id`
- `workflow_version`
- input `instruction_id`
- tool call results
- evidence bundle
- diagnosis result
- draft commentary
- policy decision
- human approval status

`experience.md` is temporary case memory. It should store examples and lessons learned until a key-value store is introduced.

## 10. Human-in-the-Loop Requirement

The system may draft commentary, but it must not finalize or send commentary without human review.

For Phase 1, the human review step can be implemented using one of the following:

- notebook cell approval
- CLI prompt
- simple function parameter such as `approval_status = "approved" | "rejected" | "needs_edit"`

The workflow should treat draft commentary as **not final** until approval is captured.

## 11. Evaluation Requirements

Create eval cases for:

1. firm short confirmed
2. incoming receive covers short
3. insufficient evidence
4. counterparty short, not firm short
5. netting mismatch

Each eval should check:

- correct scenario classification
- correct reason code
- required tools were called
- required evidence fields were retrieved
- commentary contains only supported claims
- commentary includes evidence references
- no automatic QMA send is performed
- human approval is required

## 12. Test Requirements

Create pytest tests for:

- CSV loading
- `data_dictionary.csv` consistency
- Position Tool
- Settlement Tool
- Reference Data Tool
- Trade / Netting Tool
- YAML schema validation
- firm-short workflow execution
- human-in-the-loop approval behavior
- eval runner

Tests should run with:

```bash
pytest
```

or:

```bash
make test
```

## 13. Notebook Requirement

Create:

```text
notebook/phase1_firm_short_reference_workflow.ipynb
```

The notebook should demonstrate:

1. loading CSV data
2. loading YAML configuration
3. invoking each tool independently
4. running the full workflow
5. showing the evidence bundle
6. producing the diagnosis
7. generating draft commentary
8. capturing human approval
9. running evals

The notebook should be easy for both a developer and a technology manager to run.

## 14. Commentary Design Rules

Generated commentary must be factual and grounded.

Rules:

- Every material claim must link to retrieved evidence.
- Do not expose internal source-system names.
- Do not invent numbers, statuses, counterparties, or timestamps.
- Prefer `insufficient evidence` over speculation.
- Keep QMA send as a human-controlled step in Phase 1.
- Make comments operationally useful and concise.

Example draft style:

```text
Delivery remains pending due to insufficient free inventory for [Security]. Current free position is below the pending delivery quantity as of [timestamp]. Incoming receives do not currently cover the shortfall. Desk action required: confirm cover, realignment, or release instruction.
```

## 15. Future Architecture Direction

Phase 1 CSV tools should be implemented with clean typed interfaces so they can later be replaced by REST/MCP-backed tools.

Future path:

```text
CSV-backed Python Tool
   ↓
REST-backed Tool Adapter
   ↓
MCP Server Tool
   ↓
ADK Agent uses MCP Toolset
```

Future memory path:

```text
ADK session memory
   ↓
Durable run state
   ↓
Key-value case memory
   ↓
pgvector RAG memory
```

## 16. Acceptance Criteria

Phase 1 is complete when:

- repo has clear README, AGENTS.md, sessions.md, and experience.md
- CSV data loads successfully
- `data_dictionary.csv` is used for field validation / documentation
- all four CSV-backed tools work
- YAML workflow config loads and validates
- Google ADK-oriented workflow or local fallback runner executes
- firm-short scenario produces evidence bundle
- diagnosis identifies firm short on free inventory for delivery
- draft commentary is evidence-grounded
- human approval is required
- evals run
- pytest suite passes
- notebook runs end-to-end

## 17. Install / Run

### Install

```bash
pip install -e ".[dev]"
```

This installs `settlement_agent` plus pytest and Jupyter for the notebook.

### Run tests

```bash
pytest
# or
make test
```

### Run evals

```bash
make eval
# or
python -m settlement_agent.application.evaluation_service.eval_runner
```

### Run the notebook

```bash
make notebook
# or
jupyter notebook notebook/phase1_firm_short_reference_workflow.ipynb
```

### Quick end-to-end Python entry point

```python
from settlement_agent.application.chat_service.workflow import run_workflow

state = run_workflow("SI-DLV-1001", approval_status="approved", reviewer="ops_user")
print(state.classification.scenario_label)   # firm_short
print(state.diagnosis.reason_code)           # FIRM_SHORT_FREE_INVENTORY
print(state.commentary.text)
print(state.is_final())                      # True
```

## 18. How the pieces fit

- **YAML configs** under `src/settlement_agent/config/` declare the use
  case, agents, workflow, prompts, tool I/O contracts, policy gates, and
  evals. They are the Development Plane.
- **CSV-backed tools** under `src/settlement_agent/domain/tools/`
  declare the Phase 1 contract and call into
  `infrastructure/db/csv_loader.py`. The contract is identical to
  what the future REST/MCP tool will expose.
- **Agent tree** lives under
  `src/settlement_agent/application/chat_service/` and follows the ADK
  root + sub-agent shape. `root_agent.py` orchestrates the
  Intake → Evidence → Diagnosis → Commentary → Policy/HITL chain;
  each sub-agent module exposes a deterministic `run(...)` (Phase 1)
  plus a `build_adk_agent()` factory for Phase 2 wire-up into an ADK
  `SequentialAgent`.
- **Workflow runner** in
  `src/settlement_agent/application/chat_service/workflow.py` is a
  thin entry point that calls the root agent and mirrors session
  state into an ADK `InMemorySessionService` when ADK is installed.
- **Session memory** is documented in `sessions.md`.
- **Eval runner** validates scenario classification, reason code, tool
  coverage, evidence fields, commentary constraints, no auto-QMA send,
  and human approval requirement.

## 19. Known Limitations in Phase 1

- Uses mock CSV data instead of live systems
- Does not implement MCP server/client plane
- Does not implement pgvector/RAG
- Does not persist memory beyond session and markdown files
- Does not send QMA messages
- Does not implement production security, entitlements, or audit dashboards

## 20. Recommended Phase 2 Direction

- Convert tools to REST-backed adapters
- Register tools through MCP
- Add durable run-state persistence
- Add pgvector RAG for SOP / policy memory
- Add richer eval harness with golden datasets
- Add observability dashboard
- Add policy registry
- Add user-facing review/approval workflow
- Add additional scenarios: receive fail, counterparty reject, intercompany dependency, netting mismatch
