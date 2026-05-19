"""Application layer.

Use-case services that orchestrate the domain layer (agents, tools,
prompts, memory) against infrastructure adapters.

  - chat_service:            root + sub-agents for the firm-short workflow
  - evaluation_service:      eval runner over the Phase 1 suite
  - reset_memory_service:    clears session / case memory (Phase 2 ready)
  - ingest_documents_service: placeholder for Phase 2 RAG ingest
"""
