# SKILLS.md

Guide for future Claude Code / Codex contributors working on this repo.

## 1. Project objective

Phase 1 reference implementation of an agentic settlement commentary
workflow built on:

- a **YAML-first Development Plane** for use cases, agents, prompts,
  workflows, tools, policies, and evals
- a **Google ADK runtime** (with a local fallback runner)
- **CSV-backed mock tools** under `data/`
- **session memory only** in Phase 1
- **human-in-the-loop** approval before any commentary is treated as final

Primary use case: *firm is short on free inventory for delivery*.

## 2. Phase 1 scope

In scope:

- Development Plane (YAML configuration + Python tool wrappers)
- four CSV-backed tools: position, settlement, reference data, trade/netting
- deterministic agents (Intake, Evidence, Diagnosis, Commentary, Policy/HITL)
- evals + pytest tests
- Jupyter notebook end-to-end

Out of scope:

- MCP server implementation
- REST API integrations
- pgvector / RAG memory
- automatic QMA send (QMA is human-controlled in Phase 1)
- persistent run state
- production security / entitlement

## 3. Repository structure

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
  config/{use_cases,agents,workflows,prompts,tools,policies,evals}/*.yaml
  domain/        # Pydantic models (tool I/O, evidence, session state)
  tools/         # CSV-backed tools + registry
  application/   # agents, workflow runner, eval runner
  infrastructure/# CSV loader
  utils/         # YAML loader
  llm_providers/ mcp_clients/ monitoring/ prompts/  # placeholders
tests/
  unit/ integration/ agent/
README.md
agents.md
SKILLS.md
sessions.md
experience.md
Makefile
pyproject.toml
```

## 4. Coding principles

- **Type everything** with Python type hints; prefer Pydantic models at
  tool and agent boundaries so the contract is explicit.
- **Deterministic CSV-backed tools** — every Phase 1 tool is a thin
  function over a CSV file. Keep them pure.
- **YAML drives behaviour**. If a Phase 1 rule is configurable, put it
  in YAML, not in code.
- **No internal source-system names** in prompts, commentary, or evidence.
- **No invented numbers, statuses, or timestamps** in commentary —
  every claim must reference retrieved evidence (`evidence_refs`).
- **Insufficient evidence > speculation**. If facts are missing, say so.
- **Human approval is mandatory** before any commentary is final.

## 5. How to add a new CSV-backed tool

1. Add the source CSV under `data/`.
2. Document the new file in `data/data_dictionary.csv` and `data/README.md`.
3. Add Pydantic input/output models in `src/settlement_agent/domain/models.py`.
4. Add a tool function in `src/settlement_agent/tools/<your_tool>.py` that:
   - accepts a Pydantic input,
   - filters CSV rows via `tools/base.py`,
   - returns a `ToolCallResult`.
5. Register the tool in `src/settlement_agent/tools/registry.py`.
6. Add a `tools.yaml` entry under `src/settlement_agent/config/tools/`.
7. Add a unit test in `tests/unit/test_tools.py`.

## 6. How to add a new YAML workflow

1. Drop a new workflow file in
   `src/settlement_agent/config/workflows/<name>.yaml` with a unique
   `workflow_id` and `workflow_version`.
2. Reference existing agents (or declare new ones in `agents/agents.yaml`).
3. Update `utils/yaml_loader.py` only if you need a new typed loader.
4. Wire the workflow into `application/workflow.py` (or generalise that
   runner to look up workflows by id).

## 7. How to add a new eval case

1. Edit `src/settlement_agent/config/evals/eval_cases.yaml` and add a
   new entry under `cases:`.
2. Required fields: `scenario_id`, `case_id`, `instruction_id`,
   `expected.scenario_label`, `expected.reason_code`,
   `expected.tools_called`, `expected.approval_required`.
3. Re-run `make eval` (or `pytest tests/agent/`).

## 8. How to add notebook tests

The notebook at `notebook/phase1_firm_short_reference_workflow.ipynb`
is a demonstration. Keep business logic out of it. To add a notebook
test:

1. Add the assertion in a notebook cell as plain `assert`.
2. If the assertion is generally useful, also add it to
   `tests/integration/test_workflow.py` or `tests/agent/test_eval_runner.py`.

## 9. Hard constraints

- **Do NOT** implement MCP servers/clients in Phase 1. Keep the path
  open by preserving the tool I/O contracts.
- **Do NOT** add pgvector / RAG memory in Phase 1.
- **Do NOT** add an automatic QMA send tool in Phase 1.
- **Do NOT** introduce real enterprise system names anywhere.
- **Do NOT** persist evidence or run state to disk in Phase 1.
- **Do** ensure every commentary draft is evidence-grounded.
- **Do** require human approval before marking commentary final.
- **Do** follow `data/data_dictionary.csv` for field naming.

## 10. Phase 2 path

- Replace CSV tools with REST adapters; expose via MCP.
- Add durable session-state storage; keep `SessionState` shape stable.
- Add pgvector-backed SOP / case memory.
- Add Control Plane: policy registry, eval gates, observability.
- Eventually add the User Plane workflow builder.
