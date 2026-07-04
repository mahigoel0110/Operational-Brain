"""
DepartmentCoverageService
=========================
Aggregates per-department knowledge statistics for use by the
Knowledge Gap engine and frontend rendering.

Pure rule-based. Zero external API calls. Zero cost.
"""

import logging
from typing import Dict, List, Any, Optional

from app.models.interview import InterviewAnswer, InterviewSession, InterviewProgress
from app.models.document import DocumentModel
from app.models.company_profile import CompanyProfile

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# MISSING DOCUMENT CATALOGUE
# Keyed by department; describes what the AI expects vs. what is typically absent.
# ─────────────────────────────────────────────────────────────────────────────
DEPT_MISSING_DOC_CATALOGUE: Dict[str, List[Dict[str, Any]]] = {
    "Production": [
        {"name": "Machine Operation Manual", "critical": True,
         "reason": "AI detected production machinery but no manuals are available."},
        {"name": "Process Flow Diagram", "critical": True,
         "reason": "Production flow steps mentioned in interview but no diagram uploaded."},
        {"name": "Emergency SOP", "critical": True,
         "reason": "Emergency shutdown procedure was not covered in uploaded documents."},
        {"name": "WIP Tracking Sheet", "critical": False,
         "reason": "Work-in-progress tracking was mentioned but no template exists."},
        {"name": "Production Capacity Report", "critical": False,
         "reason": "Capacity figures shared in interview lack supporting documentation."},
    ],
    "Maintenance": [
        {"name": "Calibration Records", "critical": True,
         "reason": "Machine calibration schedules are missing from the knowledge base."},
        {"name": "Breakdown Response SOP", "critical": True,
         "reason": "No breakdown escalation procedure document found."},
        {"name": "Machine Health Log Template", "critical": True,
         "reason": "Preventive maintenance logs are not uploaded."},
        {"name": "Spare Parts Inventory List", "critical": False,
         "reason": "Spare part tracking was mentioned but not documented."},
        {"name": "CMMS User Guide", "critical": False,
         "reason": "CMMS system referenced in interview without supporting documentation."},
    ],
    "Quality": [
        {"name": "Inspection Checklist", "critical": True,
         "reason": "Quality inspection steps exist in interview but no checklist document found."},
        {"name": "ISO Audit Report", "critical": True,
         "reason": "ISO standards mentioned but no audit trail documents uploaded."},
        {"name": "Defect Classification Matrix", "critical": False,
         "reason": "Defect categorization process not documented."},
        {"name": "Customer Return Analysis", "critical": False,
         "reason": "Return handling process mentioned without policy document."},
    ],
    "Safety": [
        {"name": "PPE Requirements Manual", "critical": True,
         "reason": "PPE protocols mentioned in interview but no formal manual uploaded."},
        {"name": "Hazard Identification Register", "critical": True,
         "reason": "Hazardous materials mentioned without safety data sheets."},
        {"name": "Incident Reporting Form", "critical": True,
         "reason": "Incident reporting process mentioned but no template uploaded."},
        {"name": "Safety Audit Checklist", "critical": False,
         "reason": "Safety audits were referenced without a checklist template."},
    ],
    "HR": [
        {"name": "Employee Handbook", "critical": True,
         "reason": "HR onboarding was discussed but no employee handbook exists in the knowledge base."},
        {"name": "Leave Policy Document", "critical": True,
         "reason": "Leave management was mentioned without a formal policy document."},
        {"name": "Performance Review Template", "critical": False,
         "reason": "Employee appraisal process described but no template found."},
        {"name": "Payroll Processing SOP", "critical": False,
         "reason": "Payroll system mentioned but no processing SOP uploaded."},
    ],
    "Finance": [
        {"name": "Purchase Policy", "critical": True,
         "reason": "Purchase authorization levels were mentioned but no policy document found."},
        {"name": "Invoice Workflow SOP", "critical": True,
         "reason": "Invoice processing steps described in interview without documentation."},
        {"name": "Budget Approval Matrix", "critical": False,
         "reason": "CapEx approval process mentioned but no authority matrix uploaded."},
        {"name": "Vendor Payment Terms", "critical": False,
         "reason": "Vendor payment terms referenced without a formal document."},
    ],
    "Procurement": [
        {"name": "Supplier Qualification Criteria", "critical": True,
         "reason": "Key suppliers named in interview but no vendor evaluation document."},
        {"name": "Procurement Lead Time Table", "critical": False,
         "reason": "Lead times mentioned in interview without supporting data sheet."},
        {"name": "Reorder Level Policy", "critical": False,
         "reason": "Inventory reorder levels discussed without documentation."},
    ],
    "Clinical": [
        {"name": "Patient Admission Protocol", "critical": True,
         "reason": "Admission flow described in interview but no protocol document found."},
        {"name": "Clinical Service Catalogue", "critical": False,
         "reason": "Services described verbally but no formal catalogue uploaded."},
        {"name": "Equipment Maintenance Log", "critical": True,
         "reason": "Medical equipment mentioned without maintenance records."},
    ],
    "General": [
        {"name": "Company Overview Document", "critical": False,
         "reason": "No formal company overview document detected in knowledge base."},
        {"name": "Organizational Chart", "critical": False,
         "reason": "Org structure described in interview but no chart uploaded."},
    ],
}

# Default missing docs for departments not in catalogue
DEFAULT_MISSING_DOCS: List[Dict[str, Any]] = [
    {"name": "Standard Operating Procedure (SOP)", "critical": True,
     "reason": "No SOP document found for this department."},
    {"name": "Department Process Guide", "critical": False,
     "reason": "Operational processes described in interview but not formally documented."},
]

DEPT_CRITICAL_KNOWLEDGE: Dict[str, List[str]] = {
    "Production": [
        "Emergency shutdown procedure",
        "Machine startup sequence",
        "WIP tracking method",
    ],
    "Maintenance": [
        "Preventive maintenance schedule",
        "Breakdown escalation path",
        "Critical spare parts list",
    ],
    "Quality": [
        "Defect classification criteria",
        "Customer complaint handling",
        "Inspection acceptance criteria",
    ],
    "Safety": [
        "Emergency evacuation procedure",
        "Hazard identification process",
        "Incident reporting chain",
    ],
    "HR": [
        "Employee grievance procedure",
        "Onboarding checklist",
        "Code of conduct",
    ],
    "Finance": [
        "Purchase authorization levels",
        "Month-end close process",
        "Expense reimbursement policy",
    ],
    "Procurement": [
        "Vendor selection criteria",
        "Purchase order approval workflow",
        "Emergency procurement process",
    ],
}


class DepartmentCoverageService:

    @staticmethod
    def get_missing_documents(
        dept: str,
        uploaded_doc_names: List[str]
    ) -> List[Dict[str, Any]]:
        """
        Returns list of missing documents for a department,
        filtered against what is already uploaded.
        """
        catalogue = DEPT_MISSING_DOC_CATALOGUE.get(dept, DEFAULT_MISSING_DOCS)
        uploaded_lower = {n.lower() for n in uploaded_doc_names}

        missing = []
        for doc in catalogue:
            # Simple name-based check — if any part of doc name appears in uploaded, skip it
            name_lower = doc["name"].lower()
            name_words = set(name_lower.split())
            already_uploaded = any(
                len(name_words & set(u.split())) >= max(1, len(name_words) // 2)
                for u in uploaded_lower
            )
            if not already_uploaded:
                missing.append(doc)

        return missing

    @staticmethod
    def get_critical_knowledge_gaps(
        dept: str,
        interview_answers_text: List[str]
    ) -> List[str]:
        """
        Returns list of critical knowledge topics not covered in interview answers.
        """
        critical = DEPT_CRITICAL_KNOWLEDGE.get(dept, [])
        combined_answers = " ".join(interview_answers_text).lower()

        gaps = []
        for topic in critical:
            topic_words = topic.lower().split()
            covered = sum(1 for w in topic_words if w in combined_answers)
            coverage_ratio = covered / len(topic_words) if topic_words else 1
            if coverage_ratio < 0.5:
                gaps.append(topic)

        return gaps

    @staticmethod
    async def build_department_stats(
        workspace_id: str,
        dept: str,
        knowledge_pct: int,
        confidence_pct: int,
    ) -> Dict[str, Any]:
        """
        Build a full stats dict for one department.
        """
        # Get answers for this dept
        sessions = await InterviewSession.find(
            {"workspace_id": workspace_id}
        ).to_list()

        dept_answers: List[str] = []
        for session in sessions:
            answers = await InterviewAnswer.find(
                {"session_id": str(session.id), "department": dept}
            ).to_list()
            dept_answers.extend(a.answer for a in answers)

        # Get uploaded doc names for this dept
        docs = await DocumentModel.find(
            {"workspace_id": workspace_id}
        ).to_list()
        ready_doc_names = [
            d.name for d in docs
            if d.status == "ready" and (d.department == dept or d.department is None)
        ]

        missing_docs = DepartmentCoverageService.get_missing_documents(dept, ready_doc_names)
        critical_gaps = DepartmentCoverageService.get_critical_knowledge_gaps(dept, dept_answers)

        return {
            "name": dept,
            "knowledge_pct": knowledge_pct,
            "confidence_pct": confidence_pct,
            "missing_documents": [d["name"] for d in missing_docs],
            "missing_document_details": missing_docs,
            "critical_knowledge": critical_gaps,
            "has_critical_missing": any(d["critical"] for d in missing_docs),
        }
