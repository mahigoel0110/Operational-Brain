"""
Copilot Models
==============
Sprint 9 — Industrial Intelligence Copilot

Stores conversation sessions and structured message history
per (workspace_id, user_id) pair.
"""

from datetime import datetime, UTC
from typing import List, Optional, Dict, Any
from beanie import Document
from pydantic import BaseModel, Field


class CitationRecord(BaseModel):
    """A single citation extracted from a retrieved chunk."""
    document_id: str = ""
    title: str = ""
    page_number: int = 1
    section: str = ""
    chunk_id: str = ""
    excerpt: str = ""
    score: float = 0.0
    stars: int = 3
    source_type: str = "document"  # document | interview | profile


class FailurePattern(BaseModel):
    equipment: str = ""
    pattern: str = ""
    occurrences: int = 0
    source_documents: List[str] = Field(default_factory=list)


class ComplianceSignal(BaseModel):
    standard: str = ""
    status: str = "unknown"  # present | missing | partial
    note: str = ""


class SourcesConsulted(BaseModel):
    documents_searched: int = 0
    chunks_retrieved: int = 0
    interview_answers_checked: int = 0
    graph_entities_matched: int = 0
    company_profile_used: bool = False
    response_time_ms: int = 0


class CopilotMessage(BaseModel):
    """One turn in a copilot conversation."""
    role: str                             # "user" | "assistant"
    content: str
    reasoning: Optional[str] = None
    confidence: int = 0
    risk_level: str = "none"             # none | low | medium | high
    knowledge_missing: bool = False
    missing_explanation: Optional[str] = None
    citations: List[CitationRecord] = Field(default_factory=list)
    failure_patterns: List[FailurePattern] = Field(default_factory=list)
    risk_signals: List[str] = Field(default_factory=list)
    recommended_actions: List[str] = Field(default_factory=list)
    compliance_signals: List[ComplianceSignal] = Field(default_factory=list)
    sources_consulted: Optional[SourcesConsulted] = None
    related: Dict[str, List[str]] = Field(default_factory=dict)
    suggestions: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class CopilotSession(Document):
    """Persistent conversation session for a workspace + user."""
    workspace_id: str
    user_id: str
    messages: List[CopilotMessage] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    class Settings:
        name = "copilot_sessions"
