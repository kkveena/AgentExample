# Agentic Settlement Commentary Sample CSV Data

Synthetic data for the Google ADK reference implementation use case: **firm is short on free inventory for delivery**.

Phase 1 intent:
- Development Plane first
- Pure YAML files/properties will call these CSV-backed tools later
- Google ADK runtime
- Memory Plane initially limited to session memory
- `experience.md` can store case memory until a future key-value store
- MCP Plane and QMA Draft Tool are deferred

CSV files:
- `position_data.csv` -> Position Tool
- `settlement_data.csv` -> Settlement Tool
- `reference_data.csv` -> Reference Data Tool
- `trade_netting_data.csv` -> Trade / Netting Tool
- `scenario_manifest.csv` -> optional test/eval scaffold
- `data_dictionary.csv` -> file descriptions

Primary test case: `UC-01-FIRM-SHORT`

Expected diagnosis for primary case:
- Delivery obligation is confirmed.
- Free position is below pending delivery quantity.
- Incoming receive has not settled and should not be assumed as cover.
- Commentary should be factual and evidence-backed.
- QMA draft/send remains deferred for a later tool.

Created: 2026-05-19T01:29:04Z
