"""Domain exceptions for the settlement agent."""
from __future__ import annotations


class SettlementAgentError(Exception):
    """Base class for all settlement-agent errors."""


class EvidenceMissingError(SettlementAgentError):
    """Raised when required evidence cannot be retrieved for a diagnosis."""


class UnsupportedScenarioError(SettlementAgentError):
    """Raised when the scenario classifier sees an unknown reason code."""


class ApprovalRequiredError(SettlementAgentError):
    """Raised when an attempt is made to finalize commentary without approval."""


class ToolInvocationError(SettlementAgentError):
    """Raised when an underlying tool adapter (CSV / REST / MCP) fails."""
