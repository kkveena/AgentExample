"""Infrastructure layer.

Adapters to the outside world:

  - api:            FastAPI surface (Phase 2)
  - db:             CSV / SQL access (Phase 1 uses CSV; Phase 2 adds SQL)
  - llm_providers:  Anthropic / Vertex / OpenAI client adapters
  - mcp_clients:    MCP server/client wiring
  - monitoring:     structured logging and tracing
  - config_loader:  YAML loader for the Development Plane configs
"""
