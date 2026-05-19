# Experience (Temporary Case Memory)

This file holds illustrative case memory for Phase 1 only. It will be
replaced by a structured key-value store (or pgvector-backed case
memory) in Phase 2.

**Do not** treat this file as production memory or as a system of
record. Cases here are synthetic and reference the sample CSV data in
`data/`.

## Case 1 — Approved firm-short (`UC-01-FIRM-SHORT`)

- Instruction: `SI-DLV-1001`
- Account: `ACC-DLV-001`
- Security: `SEC-US-0001` (Alpha Corp Common Stock)
- Delivery obligation: 150,000 pending
- Free position: 85,000 (insufficient)
- Pledged: 90,000; Segregated: 25,000
- Incoming receives: 0 (no cover)
- Diagnosis: `FIRM_SHORT_FREE_INVENTORY`
- Draft commentary: factual, evidence-grounded
- Human decision: **approved**
- Lesson: When free position is below pending delivery and no incoming
  receive is linked, classify as firm short and route for desk action.

## Case 2 — Insufficient evidence (`UC-01-COVERED`)

- Instruction: `SI-DLV-1003`
- Account: `ACC-DLV-002`
- Security: `SEC-US-0002` (Beta Financial Common Stock)
- Free position: 260,000 vs delivery 200,000 (sufficient)
- Diagnosis: `NO_POSITION_SHORT`
- Draft commentary: prefers "insufficient evidence" framing — no
  firm-short condition detected.
- Human decision: **needs_edit** (analyst pulls instead of system-drafted
  commentary)
- Lesson: When the firm-short condition cannot be supported by evidence,
  prefer an `insufficient_evidence` framing over speculation.

## Case 3 — Rejected draft (`UC-01-INCOMING-COVER`)

- Instruction: `SI-DLV-1005`
- Account: `ACC-DLV-004`
- Security: `SEC-US-0004` (Delta Tech Common Stock)
- Free position: 95,000 vs delivery 250,000 (short)
- Incoming receive: 180,000 expected
- Diagnosis: `SHORT_PENDING_INCOMING_RECEIVE`
- Draft commentary: notes pending incoming receive may cover
- Human decision: **rejected** because the receive had not yet settled
  at draft time and the reviewer judged external commentary premature.
- Lesson: Pending incoming receives are not cover until they settle.
  Wait for settlement confirmation before any external messaging.

## Operating notes from Phase 1

- Always prefer `insufficient_evidence` over speculation.
- Never assume QMA send. Send is human-controlled.
- Quantities and statuses must come from retrieved evidence — never
  invented in commentary text.
- Internal source-system names must never appear in commentary.

## Phase 2 migration plan

- Move these examples into a KV store keyed by `case_id`.
- Add per-case embeddings for retrieval by the Diagnosis Agent.
- Capture reviewer rationale and lesson tags as structured fields.
