"""Domain models for the settlement commentary workflow.

All models are Pydantic-typed so tool boundaries stay stable when CSV-backed
implementations are later replaced by REST/MCP-backed adapters.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


# ---------------------------------------------------------------------------
# Tool input models
# ---------------------------------------------------------------------------


class PositionToolInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    account_id: str
    security_id: Optional[str] = None
    cusip: Optional[str] = None
    isin: Optional[str] = None
    settlement_date: Optional[str] = None
    settlement_location: Optional[str] = None


class SettlementToolInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    instruction_id: Optional[str] = None
    account_id: Optional[str] = None
    security_id: Optional[str] = None
    settlement_date: Optional[str] = None


class ReferenceDataToolInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    security_id: Optional[str] = None
    cusip: Optional[str] = None
    isin: Optional[str] = None
    account_id: Optional[str] = None
    counterparty_id: Optional[str] = None


class TradeNettingToolInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    account_id: Optional[str] = None
    security_id: Optional[str] = None
    counterparty_id: Optional[str] = None
    settlement_date: Optional[str] = None


# ---------------------------------------------------------------------------
# Tool output models
# ---------------------------------------------------------------------------


class PositionEvidence(BaseModel):
    model_config = ConfigDict(extra="ignore")

    position_evidence_id: str
    account_id: str
    security_id: str
    settlement_location: Optional[str] = None
    total_position_qty: float
    free_position_qty: float
    pledged_qty: float
    segregated_qty: float
    on_loan_qty: float
    pending_receive_qty: float
    pending_delivery_qty: float
    free_short_qty: float
    inventory_status: Optional[str] = None
    snapshot_ts: Optional[str] = None
    source_latency_seconds: Optional[int] = None
    confidence_score: Optional[float] = None


class SettlementEvidence(BaseModel):
    model_config = ConfigDict(extra="ignore")

    settlement_evidence_id: str
    instruction_id: str
    trade_id: Optional[str] = None
    netting_group_id: Optional[str] = None
    account_id: str
    counterparty_id: Optional[str] = None
    security_id: str
    direction: Literal["DELIVER", "RECEIVE"]
    instruction_qty: float
    settled_qty: float
    pending_qty: float
    settlement_location: Optional[str] = None
    match_status: Optional[str] = None
    settlement_status: Optional[str] = None
    delivery_obligation_confirmed: Optional[str] = None
    counterparty_status: Optional[str] = None
    incoming_receive_linked: Optional[str] = None
    reject_code: Optional[str] = None
    fail_reason_hint: Optional[str] = None
    last_status_ts: Optional[str] = None
    confidence_score: Optional[float] = None


class ReferenceEvidence(BaseModel):
    model_config = ConfigDict(extra="ignore")

    ref_id: str
    security_id: str
    cusip: Optional[str] = None
    isin: Optional[str] = None
    symbol: Optional[str] = None
    security_description: Optional[str] = None
    asset_class: Optional[str] = None
    market: Optional[str] = None
    currency: Optional[str] = None
    settlement_cycle: Optional[str] = None
    default_settlement_location: Optional[str] = None
    eligible_for_delivery: Optional[str] = None
    account_id: Optional[str] = None
    account_type: Optional[str] = None
    counterparty_id: Optional[str] = None
    counterparty_name: Optional[str] = None
    counterparty_type: Optional[str] = None
    standard_instruction_type: Optional[str] = None
    data_as_of_ts: Optional[str] = None
    confidence_score: Optional[float] = None


class TradeNettingEvidence(BaseModel):
    model_config = ConfigDict(extra="ignore")

    trade_evidence_id: str
    trade_id: str
    netting_group_id: Optional[str] = None
    account_id: str
    counterparty_id: Optional[str] = None
    security_id: str
    side: Optional[str] = None
    gross_trade_qty: float
    netted_instruction_qty: float
    counterparty_nets_flag: Optional[str] = None
    gross_vs_net_mismatch_flag: Optional[str] = None
    netting_method: Optional[str] = None
    include_in_obligation: Optional[str] = None
    business_rule_tag: Optional[str] = None
    confidence_score: Optional[float] = None


class ToolCallResult(BaseModel):
    """Generic tool call envelope, suitable for an MCP tool result later."""

    model_config = ConfigDict(extra="forbid")

    tool_name: str
    input_payload: dict
    records: list[dict] = Field(default_factory=list)
    record_count: int = 0
    source: str = "csv_mock"
    retrieved_at: datetime = Field(default_factory=datetime.utcnow)
    error: Optional[str] = None


# ---------------------------------------------------------------------------
# Workflow / evidence models
# ---------------------------------------------------------------------------


class EvidenceBundle(BaseModel):
    model_config = ConfigDict(extra="forbid")

    instruction_id: Optional[str] = None
    case_id: Optional[str] = None
    position: list[PositionEvidence] = Field(default_factory=list)
    settlement: list[SettlementEvidence] = Field(default_factory=list)
    reference: list[ReferenceEvidence] = Field(default_factory=list)
    trade_netting: list[TradeNettingEvidence] = Field(default_factory=list)
    tool_calls: list[ToolCallResult] = Field(default_factory=list)

    def tools_called(self) -> list[str]:
        return [tc.tool_name for tc in self.tool_calls]


class ScenarioClassification(BaseModel):
    model_config = ConfigDict(extra="forbid")

    instruction_id: Optional[str] = None
    case_id: Optional[str] = None
    scenario_label: str
    is_firm_short_candidate: bool
    notes: Optional[str] = None


class DiagnosisResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    reason_code: str
    is_firm_short: bool
    delivery_obligation_qty: Optional[float] = None
    free_position_qty: Optional[float] = None
    shortfall_qty: Optional[float] = None
    pledged_qty: Optional[float] = None
    segregated_qty: Optional[float] = None
    incoming_receive_qty: Optional[float] = None
    incoming_receive_covers: bool = False
    recommended_action: str
    evidence_refs: list[str] = Field(default_factory=list)
    confidence: float = 0.0
    notes: Optional[str] = None


class CommentaryDraft(BaseModel):
    model_config = ConfigDict(extra="forbid")

    text: str
    reason_code: str
    evidence_refs: list[str] = Field(default_factory=list)
    contains_unsupported_claims: bool = False
    grounded: bool = True


ApprovalStatus = Literal["pending", "approved", "rejected", "needs_edit"]


class PolicyResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    passed: bool
    findings: list[str] = Field(default_factory=list)
    requires_human_approval: bool = True


class HumanApproval(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: ApprovalStatus = "pending"
    reviewer: Optional[str] = None
    comments: Optional[str] = None
    decided_at: Optional[datetime] = None


class SessionState(BaseModel):
    """In-memory session state that mirrors what ADK session memory will hold."""

    model_config = ConfigDict(extra="forbid")

    run_id: str
    use_case_id: str
    workflow_version: str
    instruction_id: Optional[str] = None
    classification: Optional[ScenarioClassification] = None
    evidence: Optional[EvidenceBundle] = None
    diagnosis: Optional[DiagnosisResult] = None
    commentary: Optional[CommentaryDraft] = None
    policy: Optional[PolicyResult] = None
    approval: HumanApproval = Field(default_factory=HumanApproval)
    extras: dict[str, Any] = Field(default_factory=dict)

    def is_final(self) -> bool:
        return self.approval.status == "approved"
