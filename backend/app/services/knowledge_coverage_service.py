"""
KnowledgeCoverageService
========================
Calculates how much knowledge the AI has per department,
based on interview answers and uploaded documents.

Pure rule-based. Zero external API calls. Zero cost.
"""

import logging
from typing import Dict, List, Any

from app.models.interview import InterviewAnswer, InterviewSession, InterviewProgress
from app.models.document import DocumentModel

logger = logging.getLogger(__name__)

# Expected number of questions per department that constitute "complete" coverage
DEPT_EXPECTED_QUESTIONS: Dict[str, int] = {
    "General":      6,
    "Production":   6,
    "Quality":      4,
    "Maintenance":  4,
    "Safety":       4,
    "HR":           3,
    "Finance":      3,
    "Procurement":  3,
    "Clinical":     4,
    "Pharmacy":     3,
    "Billing":      3,
    "Operations":   5,
    "Compliance":   4,
    "IT":           4,
    "Sales":        4,
    "Engineering":  4,
    "Supply Chain": 3,
}

# Weight of documents vs interview in coverage calculation (0.0 – 1.0)
DOCUMENT_WEIGHT = 0.30
INTERVIEW_WEIGHT = 0.70


class KnowledgeCoverageService:

    @staticmethod
    async def get_coverage_for_workspace(workspace_id: str) -> Dict[str, Any]:
        """
        Returns per-department coverage scores for a given workspace.

        Returns:
            {
                "departments": {
                    "Production": {"interview_pct": 83, "document_pct": 40, "combined_pct": 70},
                    ...
                },
                "overall_interview_pct": 64,
                "overall_document_pct": 30,
                "overall_combined_pct": 52
            }
        """
        # Load all interview answers for this workspace
        sessions = await InterviewSession.find(
            {"workspace_id": workspace_id}
        ).to_list()

        all_answers: List[InterviewAnswer] = []
        dept_answer_count: Dict[str, int] = {}

        for session in sessions:
            answers = await InterviewAnswer.find(
                {"session_id": str(session.id)}
            ).to_list()
            all_answers.extend(answers)

        for ans in all_answers:
            dept = ans.department or "General"
            dept_answer_count[dept] = dept_answer_count.get(dept, 0) + 1

        # Load uploaded documents for this workspace
        docs = await DocumentModel.find(
            {"workspace_id": workspace_id}
        ).to_list()

        ready_docs = [d for d in docs if d.status == "ready"]
        dept_doc_count: Dict[str, int] = {}
        for doc in ready_docs:
            dept = doc.department or "General"
            dept_doc_count[dept] = dept_doc_count.get(dept, 0) + 1

        # Determine which departments to evaluate
        all_depts = set(dept_answer_count.keys()) | set(dept_doc_count.keys())
        if not all_depts:
            all_depts = {"General"}

        dept_coverage: Dict[str, Dict[str, int]] = {}

        for dept in all_depts:
            expected = DEPT_EXPECTED_QUESTIONS.get(dept, 4)
            answered = dept_answer_count.get(dept, 0)
            doc_count = dept_doc_count.get(dept, 0)

            interview_pct = min(100, int((answered / expected) * 100))

            # Document coverage: 1 doc = 25%, 2 docs = 50%, 3+ = 75%+, capped at 95%
            doc_pct = min(95, doc_count * 25)

            combined = int(
                interview_pct * INTERVIEW_WEIGHT + doc_pct * DOCUMENT_WEIGHT
            )

            dept_coverage[dept] = {
                "interview_pct": interview_pct,
                "document_pct": doc_pct,
                "combined_pct": combined,
                "answered_questions": answered,
                "expected_questions": expected,
                "document_count": doc_count,
            }

        # Overall averages
        if dept_coverage:
            overall_interview = int(
                sum(v["interview_pct"] for v in dept_coverage.values()) / len(dept_coverage)
            )
            overall_document = int(
                sum(v["document_pct"] for v in dept_coverage.values()) / len(dept_coverage)
            )
            overall_combined = int(
                sum(v["combined_pct"] for v in dept_coverage.values()) / len(dept_coverage)
            )
        else:
            overall_interview = overall_document = overall_combined = 0

        return {
            "departments": dept_coverage,
            "overall_interview_pct": overall_interview,
            "overall_document_pct": overall_document,
            "overall_combined_pct": overall_combined,
        }
