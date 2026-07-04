"""
RecommendationService (Sprint 7)
=================================
Generates enriched document upload recommendations for a workspace.
Goes beyond the basic RecommendationEngine by adding:
  - Expected AI knowledge gain per document
  - Specific reasons based on detected company profile
  - Priority scoring (critical / high / medium / low)

Pure rule-based. Zero external API calls. Zero cost.
"""

import logging
from typing import Any, Dict, List, Optional

from app.models.interview import InterviewSession, InterviewAnswer, InterviewRecommendation
from app.models.document import DocumentModel
from app.models.company_profile import CompanyProfile

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# ENRICHED RECOMMENDATION CATALOGUE
# Structure:
#   department → list of recommendation dicts
#   Each dict: {document_name, priority, base_reason, expected_gain_pct}
# ─────────────────────────────────────────────────────────────────────────────
ENRICHED_RECOMMENDATION_CATALOGUE: Dict[str, List[Dict[str, Any]]] = {

    "General": [
        {"document_name": "Company Overview & Org Chart", "priority": "medium",
         "base_reason": "No company overview document detected. This helps the AI understand your business structure.",
         "expected_gain_pct": 4},
        {"document_name": "HR Employee Handbook", "priority": "high",
         "base_reason": "Employee policies were mentioned in the interview but no formal handbook was found.",
         "expected_gain_pct": 6},
    ],

    "Production": [
        {"document_name": "Machine Operation Manual", "priority": "critical",
         "base_reason": "AI detected production machinery but no operation manuals are available.",
         "expected_gain_pct": 9},
        {"document_name": "Production Process Flow Diagram", "priority": "critical",
         "base_reason": "Production flow steps were described in the interview but no formal diagram exists.",
         "expected_gain_pct": 8},
        {"document_name": "Emergency Shutdown SOP", "priority": "critical",
         "base_reason": "Emergency procedures are a critical safety gap — no emergency SOP was found.",
         "expected_gain_pct": 7},
        {"document_name": "WIP Tracking Template", "priority": "medium",
         "base_reason": "Work-in-progress tracking was mentioned in the interview but no template was uploaded.",
         "expected_gain_pct": 4},
        {"document_name": "Production Capacity Report", "priority": "medium",
         "base_reason": "Capacity figures were shared verbally but lack supporting documentation.",
         "expected_gain_pct": 3},
    ],

    "Maintenance": [
        {"document_name": "Equipment Calibration Records", "priority": "critical",
         "base_reason": "Machine calibration schedules are missing — the AI cannot answer calibration queries.",
         "expected_gain_pct": 8},
        {"document_name": "Breakdown Response SOP", "priority": "critical",
         "base_reason": "No breakdown escalation procedure document found in the knowledge base.",
         "expected_gain_pct": 9},
        {"document_name": "Preventive Maintenance Schedule", "priority": "high",
         "base_reason": "PM schedules were discussed in the interview but not formally uploaded.",
         "expected_gain_pct": 7},
        {"document_name": "Machine Health Log Template", "priority": "high",
         "base_reason": "Maintenance logs are not uploaded — AI cannot generate maintenance status reports.",
         "expected_gain_pct": 6},
        {"document_name": "Spare Parts Catalogue", "priority": "medium",
         "base_reason": "Spare part tracking was mentioned but not documented.",
         "expected_gain_pct": 4},
    ],

    "Quality": [
        {"document_name": "Quality Inspection Checklist", "priority": "critical",
         "base_reason": "Quality inspection steps exist in interview but no checklist document found.",
         "expected_gain_pct": 8},
        {"document_name": "ISO Audit Report", "priority": "high",
         "base_reason": "ISO standards were mentioned but no audit trail documents were uploaded.",
         "expected_gain_pct": 7},
        {"document_name": "Defect Classification Matrix", "priority": "high",
         "base_reason": "Defect categorization process was not documented — AI cannot classify quality issues.",
         "expected_gain_pct": 6},
        {"document_name": "Customer Return Analysis Template", "priority": "medium",
         "base_reason": "Return handling process mentioned without a formal policy document.",
         "expected_gain_pct": 3},
    ],

    "Safety": [
        {"document_name": "PPE Requirements Manual", "priority": "critical",
         "base_reason": "PPE protocols were mentioned in interview but no formal manual was uploaded.",
         "expected_gain_pct": 9},
        {"document_name": "Hazard Identification Register (HIRA)", "priority": "critical",
         "base_reason": "Hazardous materials were mentioned without accompanying safety data sheets.",
         "expected_gain_pct": 8},
        {"document_name": "Incident Reporting Form", "priority": "critical",
         "base_reason": "Incident reporting process was mentioned but no formal template was uploaded.",
         "expected_gain_pct": 7},
        {"document_name": "Safety Audit Checklist", "priority": "high",
         "base_reason": "Safety audits were referenced in the interview without a checklist template.",
         "expected_gain_pct": 6},
        {"document_name": "Emergency Evacuation Plan", "priority": "critical",
         "base_reason": "No evacuation plan found — this is a critical compliance requirement.",
         "expected_gain_pct": 8},
    ],

    "HR": [
        {"document_name": "Employee Handbook", "priority": "critical",
         "base_reason": "HR onboarding was discussed but no employee handbook exists in the knowledge base.",
         "expected_gain_pct": 8},
        {"document_name": "Leave Policy Document", "priority": "high",
         "base_reason": "Leave management was mentioned without a formal policy document.",
         "expected_gain_pct": 6},
        {"document_name": "Performance Review Template", "priority": "medium",
         "base_reason": "Employee appraisal process described but no evaluation template found.",
         "expected_gain_pct": 4},
        {"document_name": "Payroll Processing SOP", "priority": "medium",
         "base_reason": "Payroll system mentioned but no processing SOP was uploaded.",
         "expected_gain_pct": 3},
    ],

    "Finance": [
        {"document_name": "Purchase Authorization Policy", "priority": "critical",
         "base_reason": "Purchase authorization levels were mentioned but no policy document found.",
         "expected_gain_pct": 8},
        {"document_name": "Invoice Processing Workflow", "priority": "high",
         "base_reason": "Invoice processing steps described in interview without formal documentation.",
         "expected_gain_pct": 7},
        {"document_name": "Budget Approval Authority Matrix", "priority": "high",
         "base_reason": "CapEx approval process mentioned but no authority matrix was uploaded.",
         "expected_gain_pct": 6},
        {"document_name": "Vendor Payment Terms Document", "priority": "medium",
         "base_reason": "Vendor payment terms referenced in interview without formal documentation.",
         "expected_gain_pct": 4},
    ],

    "Procurement": [
        {"document_name": "Supplier Qualification Criteria", "priority": "high",
         "base_reason": "Key suppliers were named in interview but no vendor evaluation document exists.",
         "expected_gain_pct": 7},
        {"document_name": "Procurement Lead Time Table", "priority": "medium",
         "base_reason": "Lead times mentioned in interview without supporting data documentation.",
         "expected_gain_pct": 4},
        {"document_name": "Reorder Level Policy", "priority": "medium",
         "base_reason": "Inventory reorder levels discussed without formal policy documentation.",
         "expected_gain_pct": 3},
        {"document_name": "Purchase Order Template", "priority": "high",
         "base_reason": "PO process described but no template found in the knowledge base.",
         "expected_gain_pct": 5},
    ],

    "Clinical": [
        {"document_name": "Patient Admission Protocol", "priority": "critical",
         "base_reason": "Admission flow described in interview but no protocol document found.",
         "expected_gain_pct": 9},
        {"document_name": "Medical Equipment Maintenance Log", "priority": "critical",
         "base_reason": "Medical equipment mentioned without maintenance records.",
         "expected_gain_pct": 8},
        {"document_name": "Clinical Service Catalogue", "priority": "medium",
         "base_reason": "Services described verbally but no formal catalogue was uploaded.",
         "expected_gain_pct": 4},
    ],
}

# Priority ordering for sorting
PRIORITY_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3}


class RecommendationService:

    @staticmethod
    async def get_recommendations(workspace_id: str) -> List[Dict[str, Any]]:
        """
        Generate enriched document recommendations for a workspace.

        Returns sorted list of recommendations with:
          - document_name
          - department
          - priority
          - reason (specific to company profile if possible)
          - expected_gain_pct
          - already_uploaded (bool)
        """
        # Load existing uploaded docs
        docs = await DocumentModel.find(
            {"workspace_id": workspace_id}
        ).to_list()
        uploaded_names_lower = {d.name.lower() for d in docs}

        # Load company profile for personalization
        profile = await CompanyProfile.find_one({"workspace_id": workspace_id})

        # Load covered departments from interview
        sessions = await InterviewSession.find(
            {"workspace_id": workspace_id}
        ).to_list()

        covered_depts: set = {"General"}
        for session in sessions:
            covered_depts.add("General")
            for dept in (session.department_queue or []):
                covered_depts.add(dept)

        # Also include departments from session.progress keys
        for session in sessions:
            for dept in (session.progress or {}).keys():
                covered_depts.add(dept)

        recommendations: List[Dict[str, Any]] = []

        for dept in covered_depts:
            catalogue = ENRICHED_RECOMMENDATION_CATALOGUE.get(dept, [])
            for rec in catalogue:
                doc_name = rec["document_name"]
                doc_name_lower = doc_name.lower()
                doc_words = set(doc_name_lower.split())

                # Check if already uploaded (fuzzy match)
                already_uploaded = any(
                    len(doc_words & set(u.split())) >= max(1, len(doc_words) // 2)
                    for u in uploaded_names_lower
                )

                # Personalize reason using company profile
                reason = rec["base_reason"]
                if profile and profile.industry:
                    reason = f"[{profile.industry}] {reason}"
                if profile and profile.machines and "machine" in doc_name_lower:
                    machine_list = ", ".join(profile.machines[:2])
                    reason += f" Detected machines: {machine_list}."

                recommendations.append({
                    "document_name": doc_name,
                    "department": dept,
                    "priority": rec["priority"],
                    "reason": reason,
                    "expected_gain_pct": rec["expected_gain_pct"],
                    "already_uploaded": already_uploaded,
                })

        # Sort: critical first, then by gain descending
        recommendations.sort(
            key=lambda r: (
                PRIORITY_ORDER.get(r["priority"], 4),
                -r["expected_gain_pct"],
                r["already_uploaded"],  # not-uploaded first
            )
        )

        return recommendations

    @staticmethod
    async def get_upload_priority_queue(workspace_id: str) -> List[Dict[str, Any]]:
        """
        Returns only the top recommendations that are NOT yet uploaded,
        sorted by priority then expected gain. Used for the Upload Priority Engine.
        """
        all_recs = await RecommendationService.get_recommendations(workspace_id)
        priority_queue = [r for r in all_recs if not r["already_uploaded"]]
        return priority_queue[:10]  # top 10
