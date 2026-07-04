"""
ReadinessService
================
Calculates the overall AI Readiness Score (0–100) for a workspace.
Factors in interview completion, document coverage, company profile, and departments.

Pure rule-based. Zero external API calls. Zero cost.
"""

import logging
from typing import Dict, Any, Optional

from app.models.interview import InterviewSession, InterviewProgress, InterviewAnswer
from app.models.document import DocumentModel
from app.models.company_profile import CompanyProfile

logger = logging.getLogger(__name__)

# Score weights (must sum to 100)
WEIGHT_INTERVIEW    = 40   # points
WEIGHT_DOCUMENTS    = 30   # points
WEIGHT_PROFILE      = 15   # points
WEIGHT_DEPARTMENTS  = 15   # points

# Baseline target
TARGET_READINESS = 85

# How many extra points each uploaded doc adds (diminishing returns applied separately)
POINTS_PER_DOC = 5
MAX_DOC_POINTS = WEIGHT_DOCUMENTS  # cap at weight


class ReadinessService:

    @staticmethod
    async def calculate(workspace_id: str) -> Dict[str, Any]:
        """
        Compute AI readiness score for a workspace.

        Returns:
            {
                "current": int,          # 0–100
                "target": int,           # always 85
                "potential": int,        # what score could be if all missing docs uploaded
                "breakdown": {
                    "interview": int,
                    "documents": int,
                    "profile": int,
                    "departments": int
                },
                "gap_to_target": int,
                "missing_upload_count": int,
            }
        """
        # ── 1. Interview contribution ─────────────────────────────────────────
        interview_score = await ReadinessService._interview_score(workspace_id)

        # ── 2. Document contribution ──────────────────────────────────────────
        doc_score, missing_upload_count = await ReadinessService._document_score(workspace_id)

        # ── 3. Company profile contribution ───────────────────────────────────
        profile_score = await ReadinessService._profile_score(workspace_id)

        # ── 4. Department coverage contribution ───────────────────────────────
        dept_score = await ReadinessService._department_score(workspace_id)

        current = interview_score + doc_score + profile_score + dept_score
        current = max(0, min(100, current))

        # Potential: if all missing docs were uploaded
        potential_doc_gain = min(
            WEIGHT_DOCUMENTS - doc_score,
            missing_upload_count * POINTS_PER_DOC
        )
        potential = min(100, current + potential_doc_gain)

        return {
            "current": current,
            "target": TARGET_READINESS,
            "potential": potential,
            "breakdown": {
                "interview": interview_score,
                "documents": doc_score,
                "profile": profile_score,
                "departments": dept_score,
            },
            "gap_to_target": max(0, TARGET_READINESS - current),
            "missing_upload_count": missing_upload_count,
        }

    # ─── Private helpers ──────────────────────────────────────────────────────

    @staticmethod
    async def _interview_score(workspace_id: str) -> int:
        """Returns 0–40 based on interview completion."""
        sessions = await InterviewSession.find(
            {"workspace_id": workspace_id}
        ).to_list()

        if not sessions:
            return 0

        # Use the most complete session
        best_pct = 0
        for session in sessions:
            pct = session.completion_percentage or 0
            if pct > best_pct:
                best_pct = pct

        # Map 0–100% completion to 0–40 points
        score = int((best_pct / 100) * WEIGHT_INTERVIEW)
        return min(WEIGHT_INTERVIEW, score)

    @staticmethod
    async def _document_score(workspace_id: str):
        """Returns (0–30, missing_count) based on uploaded & ready documents."""
        docs = await DocumentModel.find(
            {"workspace_id": workspace_id}
        ).to_list()

        ready_docs = [d for d in docs if d.status == "ready"]
        failed_docs = [d for d in docs if d.status == "failed"]

        # Count distinct departments covered
        covered_depts = len(set(
            d.department for d in ready_docs if d.department
        ))

        # Base: each doc adds 5 points, capped at 30
        raw_score = min(MAX_DOC_POINTS, len(ready_docs) * POINTS_PER_DOC)

        # Penalty for failed docs
        penalty = min(10, len(failed_docs) * 3)
        score = max(0, raw_score - penalty)

        # Missing uploads = expected docs per dept × depts with no docs
        # A rough proxy for what's still needed
        from app.services.department_coverage_service import DEPT_MISSING_DOC_CATALOGUE
        expected_dept_count = covered_depts if covered_depts else 1
        missing_count = sum(
            len(DEPT_MISSING_DOC_CATALOGUE.get(dept, [])) - docs_in_dept
            for dept in list(DEPT_MISSING_DOC_CATALOGUE.keys())[:expected_dept_count]
            for docs_in_dept in [sum(1 for d in ready_docs if d.department == dept)]
            if docs_in_dept < len(DEPT_MISSING_DOC_CATALOGUE.get(dept, []))
        )
        missing_count = max(0, missing_count)

        return min(WEIGHT_DOCUMENTS, score), missing_count

    @staticmethod
    async def _profile_score(workspace_id: str) -> int:
        """Returns 0–15 based on company profile completeness."""
        profile = await CompanyProfile.find_one({"workspace_id": workspace_id})
        if not profile:
            return 0

        score = 0
        if profile.industry:
            score += 3
        if profile.company_name:
            score += 2
        if profile.departments:
            score += 3
        if profile.products:
            score += 2
        if profile.core_business:
            score += 3
        if profile.employee_count:
            score += 2

        return min(WEIGHT_PROFILE, score)

    @staticmethod
    async def _department_score(workspace_id: str) -> int:
        """Returns 0–15 based on how many departments have interview answers."""
        sessions = await InterviewSession.find(
            {"workspace_id": workspace_id}
        ).to_list()

        covered_depts: set = set()
        for session in sessions:
            answers = await InterviewAnswer.find(
                {"session_id": str(session.id)}
            ).to_list()
            for a in answers:
                dept = a.department or "General"
                if dept != "General":
                    covered_depts.add(dept)

        # Each department covered = 3 points, max 15
        score = min(WEIGHT_DEPARTMENTS, len(covered_depts) * 3)
        return score
