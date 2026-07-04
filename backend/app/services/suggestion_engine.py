"""
SuggestionEngine
=================
Sprint 9 — Industrial Intelligence Copilot

Rule-based follow-up question generator.
Produces 3 relevant follow-up questions based on query intent and industry.

Zero cost. Zero external API calls.
"""

import re
import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# FOLLOW-UP TEMPLATES BY INTENT
# ─────────────────────────────────────────────────────────────────────────────

SUGGESTIONS_BY_INTENT: dict[str, list[str]] = {
    "maintenance": [
        "Show me the inspection checklist for this equipment",
        "Who is responsible for approving maintenance work orders?",
        "What is the failure history for this equipment?",
        "Which spare parts are required for this maintenance task?",
        "What is the estimated downtime for this repair?",
        "Show me the OEM manual section for this procedure",
        "When was the last preventive maintenance performed?",
    ],
    "safety": [
        "What PPE is required for this activity?",
        "Show me the emergency response procedure",
        "What is the incident reporting process?",
        "Which safety permits are required for this work?",
        "Show me the toolbox talk checklist",
        "What hazardous materials are involved?",
        "Who is the designated safety officer for this area?",
    ],
    "compliance": [
        "Which regulatory standards apply to this process?",
        "Show me the audit checklist for this compliance area",
        "What corrective actions are required for compliance gaps?",
        "When is the next compliance audit scheduled?",
        "Who is the compliance officer responsible?",
        "What documentation is required to demonstrate compliance?",
    ],
    "quality": [
        "What are the acceptance criteria for this specification?",
        "Show me the inspection records for recent batches",
        "What is the non-conformance procedure?",
        "Which quality instruments are required for this test?",
        "What is the rejection rate trend for this process?",
        "Show me the corrective and preventive action (CAPA) log",
    ],
    "general": [
        "Which department owns this process?",
        "Show me all related SOPs and procedures",
        "What documents cover this topic?",
        "Who should I contact for more information?",
        "What training is required for this activity?",
    ],
}

# Intent detection word sets
MAINTENANCE_WORDS = {
    "maintenance", "repair", "service", "inspection", "lubrication",
    "overhaul", "replacement", "calibration", "bearing", "pump",
    "compressor", "valve", "filter", "belt", "shaft", "seal",
    "pm", "breakdown", "fault", "failure", "fix"
}
SAFETY_WORDS = {
    "safety", "hse", "hazard", "accident", "incident", "ppe",
    "emergency", "evacuation", "fire", "chemical", "toxic",
    "loto", "lockout", "permit", "safe"
}
COMPLIANCE_WORDS = {
    "compliance", "audit", "iso", "standard", "regulation",
    "factory", "oisd", "peso", "certification", "legal",
    "requirement", "policy", "compliant"
}
QUALITY_WORDS = {
    "quality", "defect", "rejection", "inspect", "tolerance",
    "specification", "qms", "rework", "scrap", "yield", "measurement"
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


class SuggestionEngine:

    @staticmethod
    def suggest(
        query: str,
        industry: Optional[str] = None,
        equipment_mentioned: Optional[List[str]] = None,
    ) -> List[str]:
        """
        Returns 3 contextual follow-up question suggestions.
        """
        intent = _detect_intent(query)
        pool = list(SUGGESTIONS_BY_INTENT.get(intent, SUGGESTIONS_BY_INTENT["general"]))

        suggestions: List[str] = []

        # If specific equipment was mentioned, add an equipment-specific suggestion first
        if equipment_mentioned:
            for equip in equipment_mentioned[:1]:
                suggestions.append(f"Show all documents related to {equip}")

        # Fill from intent pool (avoid duplicates)
        for s in pool:
            if len(suggestions) >= 3:
                break
            if s not in suggestions:
                suggestions.append(s)

        return suggestions[:3]
