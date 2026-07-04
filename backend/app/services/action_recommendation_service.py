"""
ActionRecommendationService
============================
Sprint 9 — Industrial Intelligence Copilot

Rule-based next-action generator. Produces 2–4 actionable engineering
recommendations based on:
- Query intent type (maintenance, safety, compliance, quality, general)
- Risk level
- Detected failure patterns
- Missing knowledge signals

Zero external API calls.
"""

import re
import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# QUERY INTENT DETECTION
# ─────────────────────────────────────────────────────────────────────────────

MAINTENANCE_WORDS = {
    "maintenance", "repair", "service", "inspection", "lubrication",
    "overhaul", "replacement", "calibration", "bearing", "pump",
    "compressor", "valve", "filter", "belt", "shaft", "seal", "pm", "breakdown"
}

SAFETY_WORDS = {
    "safety", "hse", "hazard", "accident", "incident", "ppe", "emergency",
    "evacuation", "fire", "chemical", "toxic", "loto", "lockout", "permit"
}

COMPLIANCE_WORDS = {
    "compliance", "audit", "iso", "standard", "regulation", "factory act",
    "oisd", "peso", "certification", "legal", "requirement", "policy"
}

QUALITY_WORDS = {
    "quality", "defect", "rejection", "inspection", "tolerance", "specification",
    "qms", "iso 9001", "rework", "scrap", "yield", "measurement"
}


def _detect_intent(query: str) -> str:
    lower = set(re.findall(r'\w+', query.lower()))
    scores = {
        "maintenance":  len(lower & MAINTENANCE_WORDS),
        "safety":       len(lower & SAFETY_WORDS),
        "compliance":   len(lower & COMPLIANCE_WORDS),
        "quality":      len(lower & QUALITY_WORDS),
    }
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else "general"


# ─────────────────────────────────────────────────────────────────────────────
# ACTION TEMPLATES PER INTENT
# ─────────────────────────────────────────────────────────────────────────────

ACTIONS_BY_INTENT = {
    "maintenance": [
        "Review the preventive maintenance schedule and verify all tasks are current",
        "Cross-reference with the OEM manual for manufacturer-recommended intervals",
        "Check maintenance work orders for any overdue tasks",
        "Verify spare parts availability before scheduling downtime",
        "Document the maintenance activity in the CMMS after completion",
    ],
    "safety": [
        "Verify all personnel have completed the required safety training",
        "Ensure PPE requirements are posted at the work area",
        "Review the emergency response procedure for this scenario",
        "Conduct a toolbox talk with the team before starting work",
        "Confirm the Permit to Work (PTW) system is activated if required",
    ],
    "compliance": [
        "Initiate an internal audit against the identified standard",
        "Document the compliance gap with a corrective action plan",
        "Assign a responsible person and target date for the corrective action",
        "Review all related documentation for compliance alignment",
        "Schedule a management review of the compliance status",
    ],
    "quality": [
        "Review the inspection criteria against the documented specification",
        "Initiate a non-conformance report (NCR) if a defect is confirmed",
        "Perform root cause analysis before releasing corrective actions",
        "Update the control plan if the process has changed",
        "Verify measurement equipment is within calibration date",
    ],
    "general": [
        "Review the related Standard Operating Procedure (SOP) for this activity",
        "Consult the department head for any additional context",
        "Upload any relevant documents to improve future answers",
        "Log the query and response in the lessons learned register",
    ],
}

RISK_HIGH_PREFIX = [
    "⚠ IMMEDIATE: Stop operation and assess safety before proceeding",
    "Escalate to maintenance supervisor and plant manager immediately",
]

RISK_MEDIUM_PREFIX = [
    "Schedule inspection at the earliest opportunity — do not defer",
]

MISSING_KNOWLEDGE_SUFFIX = [
    "Upload the relevant document to OperationalBrain to improve answer accuracy",
]


class ActionRecommendationService:

    @staticmethod
    def recommend(
        query: str,
        risk_level: str,
        knowledge_missing: bool,
        failure_patterns: List[Dict[str, Any]],
        equipment_mentioned: List[str] = None,
    ) -> List[str]:
        """
        Returns 2–4 actionable recommendations.
        """
        intent = _detect_intent(query)
        base_actions = list(ACTIONS_BY_INTENT.get(intent, ACTIONS_BY_INTENT["general"]))

        actions: List[str] = []

        # 1. Risk prefix (if high or medium risk)
        if risk_level == "high":
            actions.extend(RISK_HIGH_PREFIX)
        elif risk_level == "medium":
            actions.extend(RISK_MEDIUM_PREFIX)

        # 2. Failure-pattern-specific actions
        if failure_patterns:
            for fp in failure_patterns[:1]:
                equip = fp.get("equipment", "the equipment")
                actions.append(
                    f"Investigate recurring issue on {equip} — "
                    f"{fp.get('occurrences', 2)} occurrences detected across uploaded documents"
                )

        # 3. Equipment-specific actions
        if equipment_mentioned:
            for equip in equipment_mentioned[:1]:
                actions.append(
                    f"Pull the maintenance history and inspection records for {equip}"
                )

        # 4. Intent-based actions (fill up to 4 total)
        for action in base_actions:
            if len(actions) >= 4:
                break
            if action not in actions:
                actions.append(action)

        # 5. Knowledge missing suffix
        if knowledge_missing:
            actions.append(MISSING_KNOWLEDGE_SUFFIX[0])

        return actions[:5]   # never more than 5
