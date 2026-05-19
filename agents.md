# AGENTS.md

Guidance for coding agents working on this repository.

## 1. Project Objective

Build a Phase 1 reference implementation for an agentic settlement commentary workflow using **Google ADK** as the runtime and a **YAML-first Development Plane**.

Primary use case:

> **Firm is short on free inventory for delivery.**

The system should collect evidence, diagnose the settlement fail scenario, draft factual commentary, and route the draft for human approval.

The system must not automatically send QMA messages in Phase 1.

## 2. Operating Principles

When modifying this repo:

1. Preserve the Phase 1 scope.
2. Keep implementation simple, working, and testable.
3. Use YAML for configuration wherever practical.
4. Keep business rules isolated from notebooks.
5. Keep tool interfaces typed and future-ready for MCP.
6. Use `data/data_dictionary.csv` as the authoritative reference for fields.
7. Do not expose internal system names in generated commentary.
8. Do not invent facts, quantities, statuses, or timestamps.
9. Prefer `insufficient evidence` over speculation.
10. Require human approval before any commentary is marked final.

## 3. Phase 1 Scope

### In scope

- Development Plane
- YAML files and properties
- Google ADK-oriented runtime
- CSV-backed tools
- session memory
- `experience.md` temporary case memory
- lightweight human-in-the-loop approval
- evals
- tests
- Jupyter notebook

### Out of scope

- MCP server implementation
- live REST API integration
- pgvector / RAG memory
- automatic QMA send
- full UI / User Plane
- production-grade security / entitlementing
- persistent database-backed run state

## 4. Expected Repository Structure

Prefer this layout. If the repo already has a structure, adapt to it instead of replacing it.

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
src/<package_name>/
  config/
    use_cases/
    agents/
    workflows/
    prompts/
    tools/
    policies/
    evals/
  domain/
  prompts/
  tools/
  utils/
  application/
  infrastructure/
  llm_providers/
  mcp_clients/
  monitoring/
tests/
  unit/
  integration/
  agent/
Makefile
Dockerfile
docker-compose.yml
pyproject.toml
README.md
AGENTS.md
sessions.md
experience.md
```

## 5. Data Rules

The `data/` directory is central to Phase 1.

Required files:

```text
data/README.md
data/data_dictionary.csv
data/position_data.csv
data/settlement_data.csv
data/reference_data.csv
data/trade_netting_data.csv
data/scenario_manifest.csv
```

Rules:

- Always inspect `data/data_dictionary.csv` before implementing or changing tools.
- Align tool input and output field names to the data dictionary.
- Keep data synthetic and generic.
- Do not add real client, counterparty, account, or production identifiers.
- Document all joins and assumptions in `data/README.md`.

## 6. Tool Implementation Rules

Implement these CSV-backed tools:

1. Position Tool
2. Settlement Tool
3. Reference Data Tool
4. Trade / Netting Tool

Do not implement QMA Draft Tool in Phase 1.

Tool design requirements:

- Use typed input and output models, preferably Pydantic.
- Use deterministic logic.
- Return structured evidence, not free-form text only.
- Include source timestamp where available.
- Include confidence / evidence quality where available.
- Include clean error handling for missing data.
- Add TODO comments showing how the CSV-backed implementation will later be replaced by REST/MCP.

Future direction:

```text
CSV-backed tool
   ↓
REST-backed adapter
   ↓
MCP server tool
   ↓
ADK MCP Toolset integration
```

## 7. Agent Workflow

The Phase 1 workflow should include these logical agents:

| Agent | Responsibility |
|---|---|
| Intake Agent | Classify the settlement scenario and extract instruction context |
| Evidence Agent | Call position, settlement, reference data, and trade/netting tools |
| Diagnosis Agent | Apply firm-short business rules |
| Commentary Agent | Draft factual commentary from evidence |
| Policy / HITL Agent | Validate constraints and route to human approval |

Use Google ADK where feasible. If ADK integration cannot be completed in one pass, create a local fallback runner that follows the same interface and keeps the notebook/tests working.

## 8. Session Memory

Create or update `sessions.md` to document Phase 1 memory.

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

Do not implement pgvector, RAG, or durable memory in Phase 1.

## 9. experience.md

Create or update `experience.md` as temporary case memory.

Include at least:

- one approved firm-short case example
- one insufficient-evidence case example
- one rejected-draft case example
- lessons learned
- note that this file will later move to a key-value store

Do not treat `experience.md` as production memory.

## 10. Human-in-the-Loop Requirement

The workflow must require human approval before finalizing commentary.

Acceptable Phase 1 approaches:

- notebook approval cell
- CLI input
- function parameter such as `approval_status = "approved" | "rejected" | "needs_edit"`

The workflow must not perform automatic QMA send.

## 11. Commentary Rules

Generated commentary must be factual, concise, and evidence-grounded.

Rules:

- Every material statement must be supported by evidence.
- Include evidence references or evidence IDs.
- Do not expose source-system names.
- Do not include unsupported numeric claims.
- Do not speculate about counterparty behavior.
- Prefer `insufficient evidence` when facts are missing.
- Keep the QMA send step outside Phase 1.

Example style:

```text
Delivery remains pending due to insufficient free inventory for [Security]. Current free position is below the pending delivery quantity as of [timestamp]. Incoming receives do not currently cover the shortfall. Desk action required: confirm cover, realignment, or release instruction.
```

## 12. YAML Configuration Requirements

Create YAML config for:

- use case
- agents
- workflow
- prompts
- tools
- policies
- evals

Suggested folders:

```text
src/<package_name>/config/use_cases/
src/<package_name>/config/agents/
src/<package_name>/config/workflows/
src/<package_name>/config/prompts/
src/<package_name>/config/tools/
src/<package_name>/config/policies/
src/<package_name>/config/evals/
```

Business rules should be represented in YAML where practical, or in clearly isolated domain modules.

## 13. Evals

Create evals for:

1. firm short confirmed
2. incoming receive covers short
3. insufficient evidence
4. counterparty short, not firm short
5. netting mismatch

Each eval case should define:

- input instruction/scenario
- expected reason code
- expected tools called
- required evidence fields
- expected approval route
- commentary constraints

The eval runner should check:

- scenario classification
- reason code
- tool call coverage
- evidence field coverage
- factuality constraints
- no automatic QMA send
- human approval required

## 14. Tests

Create pytest tests for:

- CSV loading
- data dictionary consistency
- Position Tool
- Settlement Tool
- Reference Data Tool
- Trade / Netting Tool
- YAML schema validation
- firm-short workflow execution
- human-in-the-loop behavior
- eval runner

Tests should run using:

```bash
pytest
```

or:

```bash
make test
```

## 15. Notebook

Create:

```text
notebook/phase1_firm_short_reference_workflow.ipynb
```

The notebook should show:

1. data load
2. YAML load
3. individual tool calls
4. workflow run
5. evidence bundle
6. diagnosis
7. draft commentary
8. human approval
9. eval execution

Keep the notebook as a demonstration, not the place where core business logic lives.

## 16. Documentation Requirements

Ensure these files exist and are useful:

```text
README.md
AGENTS.md
data/README.md
sessions.md
experience.md
```

README.md should explain how to install, test, and run the notebook.

AGENTS.md should guide future coding agents.

data/README.md should explain sample data and tool mapping.

sessions.md should explain session memory.

experience.md should hold temporary case memory examples.

## 17. Coding Style

Use:

- Python type hints
- Pydantic models where useful
- small, testable functions
- clear docstrings
- deterministic CSV-backed tools
- isolated business rules
- explicit errors for missing data
- simple interfaces that can later become MCP tools

Avoid:

- hard-coded one-off logic in notebooks
- hidden global state
- real enterprise system names
- unsupported commentary claims
- premature MCP / RAG implementation
- automatic QMA send

## 18. Completion Summary Required

After making changes, summarize:

- files created
- files modified
- how to run tests
- how to run notebook
- known limitations
- recommended next steps

## 19. Definition of Done for Phase 1

Phase 1 is done when:

- CSV data loads
- `data_dictionary.csv` is respected
- tools return structured evidence
- YAML workflow loads and validates
- workflow runs end-to-end
- firm-short diagnosis works
- draft commentary is generated
- human approval is required
- evals run
- tests pass
- notebook demonstrates the flow
- README / AGENTS / sessions / experience docs are present
