"""
KnowledgeGapService
====================
Core engine for Sprint 7 — Knowledge Gap Analysis.

Orchestrates KnowledgeCoverageService, DepartmentCoverageService,
RecommendationService, and ReadinessService to produce the full
gap analysis payload.

Pure rule-based. Zero external API calls. Zero cost.
"""

import logging
from typing import Any, Dict, List

from app.models.company_profile import CompanyProfile
from app.models.interview import InterviewSession, InterviewAnswer
from app.models.document import DocumentModel
from app.services.knowledge_coverage_service import KnowledgeCoverageService
from app.services.department_coverage_service import DepartmentCoverageService
from app.services.readiness_service import ReadinessService

logger = logging.getLogger(__name__)

# Confidence is generally 0.85x the knowledge pct (AI is less confident
# than it is knowledgeable, because knowledge can be partial/outdated).
CONFIDENCE_RATIO = 0.85

# Health thresholds
HEALTH_HEALTHY_THRESHOLD  = 75
HEALTH_MODERATE_THRESHOLD = 45


class KnowledgeGapService:

    @staticmethod
    async def get_full_analysis(workspace_id: str) -> Dict[str, Any]:
        """
        Full gap analysis for a workspace.

        Returns:
          {
            "workspace_id": ...,
            "departments": [DeptGapReport, ...],
            "overall_knowledge_pct": int,
            "overall_confidence_pct": int,
            "generated_at": str
          }
        """
        from datetime import datetime, UTC

        # ── 1. Coverage scores ───────────────────────────────────────────────
        coverage = await KnowledgeCoverageService.get_coverage_for_workspace(workspace_id)
        dept_coverage: Dict[str, Dict] = coverage["departments"]

        # ── 2. Ensure we have at least the profile departments ───────────────
        profile = await CompanyProfile.find_one({"workspace_id": workspace_id})
        if profile and profile.departments:
            for dept in profile.departments:
                if dept not in dept_coverage:
                    dept_coverage[dept] = {
                        "interview_pct": 0,
                        "document_pct": 0,
                        "combined_pct": 0,
                        "answered_questions": 0,
                        "expected_questions": 4,
                        "document_count": 0,
                    }

        # Filter out "General" from the displayed results unless it's the only dept
        display_depts = [d for d in dept_coverage if d != "General"]
        if not display_depts:
            display_depts = list(dept_coverage.keys())

        # ── 3. Build per-department report ───────────────────────────────────
        dept_reports = []
        for dept in display_depts:
            stats = dept_coverage[dept]
            knowledge_pct = stats["combined_pct"]
            # Confidence is slightly lower than raw knowledge %
            confidence_pct = max(0, min(100, int(knowledge_pct * CONFIDENCE_RATIO)))

            dept_stats = await DepartmentCoverageService.build_department_stats(
                workspace_id=workspace_id,
                dept=dept,
                knowledge_pct=knowledge_pct,
                confidence_pct=confidence_pct,
            )
            dept_reports.append(dept_stats)

        # Sort: lowest knowledge first (gaps are most visible)
        dept_reports.sort(key=lambda d: d["knowledge_pct"])

        # ── 4. Overall aggregates ────────────────────────────────────────────
        if dept_reports:
            overall_knowledge = int(
                sum(d["knowledge_pct"] for d in dept_reports) / len(dept_reports)
            )
            overall_confidence = int(
                sum(d["confidence_pct"] for d in dept_reports) / len(dept_reports)
            )
        else:
            overall_knowledge = coverage.get("overall_combined_pct", 0)
            overall_confidence = int(overall_knowledge * CONFIDENCE_RATIO)

        return {
            "workspace_id": workspace_id,
            "departments": dept_reports,
            "overall_knowledge_pct": overall_knowledge,
            "overall_confidence_pct": overall_confidence,
            "generated_at": datetime.now(UTC).isoformat(),
        }

    @staticmethod
    async def get_health(workspace_id: str) -> Dict[str, Any]:
        """
        Returns Knowledge Health status.

        Returns:
          {
            "status": "Healthy" | "Moderate" | "Poor",
            "color": "emerald" | "amber" | "red",
            "score": int,
            "reasons": [str, ...]
          }
        """
        readiness = await ReadinessService.calculate(workspace_id)
        score = readiness["current"]

        # Gather specific reasons
        reasons: List[str] = []
        coverage = await KnowledgeCoverageService.get_coverage_for_workspace(workspace_id)
        dept_coverage = coverage["departments"]

        for dept, stats in dept_coverage.items():
            if dept == "General":
                continue
            combined = stats["combined_pct"]
            if combined < 40:
                reasons.append(f"{dept} documentation is critically incomplete ({combined}% covered).")
            elif combined < 65:
                reasons.append(f"{dept} documentation is incomplete ({combined}% covered).")

        # Check for failed documents
        docs = await DocumentModel.find({"workspace_id": workspace_id}).to_list()
        failed = [d for d in docs if d.status == "failed"]
        if failed:
            reasons.append(f"{len(failed)} document(s) failed to process — re-upload required.")

        # Company profile check
        profile = await CompanyProfile.find_one({"workspace_id": workspace_id})
        if not profile or not profile.industry:
            reasons.append("Company profile is incomplete — industry not yet identified.")

        # Interview check
        sessions = await InterviewSession.find({"workspace_id": workspace_id}).to_list()
        if not sessions:
            reasons.append("No AI interview has been conducted for this workspace.")
        else:
            incomplete = [s for s in sessions if s.status != "completed"]
            if len(incomplete) == len(sessions):
                reasons.append("AI onboarding interview has not been completed.")

        # Determine status
        if score >= HEALTH_HEALTHY_THRESHOLD:
            status = "Healthy"
            color = "emerald"
        elif score >= HEALTH_MODERATE_THRESHOLD:
            status = "Moderate"
            color = "amber"
        else:
            status = "Poor"
            color = "red"

        # If no specific reasons found but status not healthy
        if not reasons:
            if status == "Healthy":
                reasons.append("All departments have adequate documentation and interview coverage.")
            elif status == "Moderate":
                reasons.append("Some departments may benefit from additional documentation.")
            else:
                reasons.append("Knowledge base requires significant improvement before AI can be effective.")

        return {
            "status": status,
            "color": color,
            "score": score,
            "reasons": reasons[:5],  # cap at 5 reasons for UX
        }
