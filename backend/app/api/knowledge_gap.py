"""
Knowledge Gap API
=================
Sprint 7 — Knowledge Gap Analysis Engine

Routes:
  GET /knowledge-gap/{workspace_id}/analysis        — full dept-by-dept gap analysis
  GET /knowledge-gap/{workspace_id}/recommendations — enriched document recommendations
  GET /knowledge-gap/{workspace_id}/readiness       — AI readiness score (0–100)
  GET /knowledge-gap/{workspace_id}/health          — knowledge health (Healthy/Moderate/Poor)
"""

from fastapi import APIRouter, Depends, HTTPException
from typing import Any, Dict

from app.core.dependencies import get_current_user
from app.models.user import User
from app.models.workspace import Workspace
from app.services.knowledge_gap_service import KnowledgeGapService
from app.services.recommendation_service import RecommendationService
from app.services.readiness_service import ReadinessService

router = APIRouter()


async def _validate_workspace(workspace_id: str) -> None:
    """Raise 404 if workspace not found."""
    ws = await Workspace.get(workspace_id)
    if not ws:
        raise HTTPException(status_code=404, detail="Workspace not found")


# ─────────────────────────────────────────────────────────────────────────────
# FULL GAP ANALYSIS
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/{workspace_id}/analysis")
async def get_gap_analysis(
    workspace_id: str,
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Returns per-department knowledge gap analysis:
    - Knowledge % and confidence % per department
    - Missing documents per department
    - Critical knowledge gaps
    - Overall summary
    """
    await _validate_workspace(workspace_id)
    return await KnowledgeGapService.get_full_analysis(workspace_id)


# ─────────────────────────────────────────────────────────────────────────────
# DOCUMENT RECOMMENDATIONS
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/{workspace_id}/recommendations")
async def get_recommendations(
    workspace_id: str,
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Returns enriched document upload recommendations:
    - Document name & department
    - Priority (critical / high / medium)
    - Specific reason based on company profile
    - Expected AI knowledge gain %
    - Whether document is already uploaded
    """
    await _validate_workspace(workspace_id)
    recommendations = await RecommendationService.get_recommendations(workspace_id)
    upload_queue = await RecommendationService.get_upload_priority_queue(workspace_id)

    return {
        "workspace_id": workspace_id,
        "recommendations": recommendations,
        "upload_priority_queue": upload_queue,
        "total_count": len(recommendations),
        "pending_count": len([r for r in recommendations if not r["already_uploaded"]]),
    }


# ─────────────────────────────────────────────────────────────────────────────
# AI READINESS SCORE
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/{workspace_id}/readiness")
async def get_readiness(
    workspace_id: str,
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Returns AI readiness score (0–100) with breakdown:
    - current: overall score based on interview + docs + profile
    - target: 85 (production-ready threshold)
    - potential: score achievable if missing docs are uploaded
    - breakdown: per-factor contribution
    - gap_to_target: points needed to reach target
    """
    await _validate_workspace(workspace_id)
    return await ReadinessService.calculate(workspace_id)


# ─────────────────────────────────────────────────────────────────────────────
# KNOWLEDGE HEALTH
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/{workspace_id}/health")
async def get_knowledge_health(
    workspace_id: str,
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Returns knowledge health assessment:
    - status: Healthy / Moderate / Poor
    - color: emerald / amber / red
    - score: readiness score
    - reasons: list of specific explanations for the health status
    """
    await _validate_workspace(workspace_id)
    return await KnowledgeGapService.get_health(workspace_id)
