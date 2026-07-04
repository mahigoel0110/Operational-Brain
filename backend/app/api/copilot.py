"""
Copilot API
============
Sprint 9 — Industrial Intelligence Copilot

Routes:
  POST /copilot/{workspace_id}/query   — main intelligence query
  GET  /copilot/{workspace_id}/history — conversation history
  DELETE /copilot/{workspace_id}/history — clear conversation
"""

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.core.dependencies import get_current_user
from app.models.copilot import CopilotSession
from app.models.user import User
from app.models.workspace import Workspace
from app.services.copilot_orchestrator import CopilotOrchestrator

logger = logging.getLogger(__name__)
router = APIRouter()


# ─────────────────────────────────────────────────────────────────────────────
# REQUEST SCHEMAS
# ─────────────────────────────────────────────────────────────────────────────

class DocumentContextRequest(BaseModel):
    document_id: str = ""
    document_name: str = ""
    excerpt: str = ""


class CopilotQueryRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    document_context: Optional[DocumentContextRequest] = None


# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────

async def _validate_workspace(workspace_id: str) -> Workspace:
    ws = await Workspace.get(workspace_id)
    if not ws:
        raise HTTPException(status_code=404, detail="Workspace not found")
    return ws


# ─────────────────────────────────────────────────────────────────────────────
# QUERY — main endpoint
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/{workspace_id}/query")
async def query_copilot(
    workspace_id: str,
    req: CopilotQueryRequest,
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Main Industrial Intelligence Copilot endpoint.

    Runs the full pipeline:
      Query Expansion → Knowledge Retrieval → LLM Reasoning →
      Evidence/Citations → Risk Assessment → Actions → Confidence → Suggestions

    Returns a fully structured response with:
    - answer, reasoning, confidence, risk_level
    - citations with star ratings
    - failure patterns (if detected)
    - compliance signals
    - recommended actions
    - follow-up suggestions
    - sources consulted (counts + timing)
    """
    await _validate_workspace(workspace_id)

    if not req.message or not req.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    doc_ctx = None
    if req.document_context and req.document_context.document_id:
        doc_ctx = {
            "document_id":   req.document_context.document_id,
            "document_name": req.document_context.document_name,
            "excerpt":       req.document_context.excerpt,
        }

    try:
        result = await CopilotOrchestrator.answer(
            workspace_id=workspace_id,
            user_id=str(current_user.id),
            message=req.message.strip(),
            session_id=req.session_id,
            document_context=doc_ctx,
        )
        return result
    except Exception as e:
        logger.error(f"Copilot query failed for workspace {workspace_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Copilot reasoning error: {str(e)}"
        )


# ─────────────────────────────────────────────────────────────────────────────
# HISTORY — fetch conversation
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/{workspace_id}/history")
async def get_history(
    workspace_id: str,
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Returns the most recent conversation session for this user + workspace.
    Returns empty history if no session exists yet.
    """
    await _validate_workspace(workspace_id)

    session = await CopilotSession.find_one({
        "workspace_id": workspace_id,
        "user_id":      str(current_user.id),
    })

    if not session:
        return {"session_id": None, "messages": []}

    # Serialize messages to plain dicts
    messages = []
    for msg in session.messages:
        messages.append({
            "role":              msg.role,
            "content":           msg.content,
            "reasoning":         msg.reasoning,
            "confidence":        msg.confidence,
            "risk_level":        msg.risk_level,
            "knowledge_missing": msg.knowledge_missing,
            "citations":         [c.model_dump() for c in msg.citations],
            "failure_patterns":  [fp.model_dump() for fp in msg.failure_patterns],
            "risk_signals":      msg.risk_signals,
            "recommended_actions": msg.recommended_actions,
            "compliance_signals": [cs.model_dump() for cs in msg.compliance_signals],
            "sources_consulted": msg.sources_consulted.model_dump() if msg.sources_consulted else None,
            "related":           msg.related,
            "suggestions":       msg.suggestions,
            "created_at":        msg.created_at.isoformat(),
        })

    return {
        "session_id": str(session.id),
        "messages":   messages,
    }


# ─────────────────────────────────────────────────────────────────────────────
# CLEAR — delete conversation history
# ─────────────────────────────────────────────────────────────────────────────

@router.delete("/{workspace_id}/history")
async def clear_history(
    workspace_id: str,
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """Clears the conversation history for this user + workspace."""
    await _validate_workspace(workspace_id)

    session = await CopilotSession.find_one({
        "workspace_id": workspace_id,
        "user_id":      str(current_user.id),
    })

    if session:
        session.messages = []
        await session.save()

    return {"cleared": True}
