# Sample CSV Data (Phase 1)

Synthetic CSV data backing the Phase 1 reference implementation for the
use case: **firm is short on free inventory for delivery**.

Phase 1 intent:

- Development Plane first.
- Pure YAML files / properties call these CSV-backed tools via the
  `settlement_agent` Python package.
- Google ADK is the runtime; a local fallback runner is provided.
- Memory Plane is limited to session memory.
- `experience.md` is temporary case memory until a Phase 2 KV store.
- MCP Plane and QMA Draft Tool are deferred.

## 1. Files and their owning tools

| CSV | Owning Tool | Purpose |
|---|---|---|
| `position_data.csv` | `position_tool` | Position evidence: free, pledged, segregated, on-loan, pending receive, pending delivery |
| `settlement_data.csv` | `settlement_tool` | Settlement instruction evidence: direction, instruction qty, settled / pending qty, match status, settlement status, counterparty status, reject code |
| `reference_data.csv` | `reference_data_tool` | Security, account, and counterparty reference attributes |
| `trade_netting_data.csv` | `trade_netting_tool` | Gross vs netted quantities and netting status |
| `scenario_manifest.csv` | (test / eval scaffold) | Maps `case_id` → primary reason code, expected action, and required tools |
| `data_dictionary.csv` | (documentation) | Authoritative file-level description for the CSV set |

## 2. Important join keys

| Field | Used by | Notes |
|---|---|---|
| `case_id` | all evidence CSVs and `scenario_manifest.csv` | Groups records that belong to the same synthetic scenario |
| `instruction_id` | `settlement_data.csv` | Primary handle from the workflow input |
| `account_id` | position, settlement, reference, trade/netting | Cross-reference for position vs settlement evidence |
| `security_id` (and `cusip`) | position, settlement, reference, trade/netting | Cross-reference for instrument level evidence |
| `counterparty_id` | settlement, reference, trade/netting | Used by Reference Data Tool and Trade/Netting Tool |
| `netting_group_id` | settlement, trade/netting | Identifies the netting group |
| `trade_id` | settlement, trade/netting | Links a settlement instruction to its underlying trade |

## 3. Synthetic data assumptions

- All quantities, prices, and identifiers are synthetic and generic.
- No real client, counterparty, account, or production identifier is used.
- No internal source-system name is referenced.
- All snapshots are dated `2026-05-18` (T) with settlement on the same
  business date. The reference workflow does not assume specific
  intraday cut-offs.
- Each `case_id` is designed to drive a deterministic diagnosis. See
  `scenario_manifest.csv` for the expected reason code and recommended
  action per case.

## 4. `data_dictionary.csv` usage

`data_dictionary.csv` is the authoritative file-level reference. Any
new CSV added in this directory must also be registered there. Tests
in `tests/unit/test_csv_loading.py` enforce that every Phase 1 CSV is
listed in `data_dictionary.csv`.

Field-level documentation lives alongside the Pydantic models in
`src/settlement_agent/domain/models.py`.

## 5. Migration path to REST / MCP

Each Phase 1 tool function is a thin wrapper that filters CSV rows. The
function signature is the contract that will be preserved in Phase 2:

```text
CSV-backed Python Tool
   ↓ (same input/output Pydantic model)
REST-backed Tool Adapter
   ↓ (registered in MCP server)
MCP Server Tool
   ↓ (consumed by Google ADK MCP Toolset)
ADK sub-agent
```

When migrating, the CSV reads in `infrastructure/csv_loader.py` should
be the only thing replaced. Domain models, tool registry, and YAML
configuration should remain unchanged.
