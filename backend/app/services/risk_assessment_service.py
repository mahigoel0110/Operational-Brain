"""
RiskAssessmentService
======================
Sprint 9 — Industrial Intelligence Copilot

Rule-based risk detection. Scans retrieved chunks for:
- Equipment failure signals
- Repeated failure patterns across multiple documents
- Compliance gap signals

Zero external API calls. Pure text analysis.
"""

import re
import logging
from collections import defaultdict
from typing import Any, Dict, List, Tuple

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# KEYWORD DICTIONARIES
# ─────────────────────────────────────────────────────────────────────────────

HIGH_RISK_KEYWORDS = {
    "failed", "failure", "breakdown", "critical", "emergency",
    "overheating", "overheat", "exceeded limit", "damage", "damaged",
    "fault", "trip", "alarm", "fire", "explosion", "leak", "spillage",
    "rupture", "corrosion", "fracture", "severe", "critical failure",
    "unsafe", "hazard", "accident", "injury", "fatality",
}

MEDIUM_RISK_KEYWORDS = {
    "warning", "degraded", "worn", "wear", "vibration", "noise",
    "temperature rise", "pressure drop", "delayed", "overdue",
    "inspection due", "maintenance required", "near miss", "deviation",
    "non-conformance", "defect", "rejected", "rework",
}

MISSING_KNOWLEDGE_KEYWORDS = {
    "not documented", "not available", "no record", "missing document",
    "not found", "not uploaded", "not provided", "unknown", "undocumented",
    "no procedure", "no sop", "no policy",
}

# Equipment tag regex: Pump P-101, Valve V-22, etc.
_EQUIP_RE = re.compile(r'\b([A-Za-z]{1,2}-?\d{2,4})\b')


def _find_risk_keywords(text: str) -> Tuple[str, List[str]]:
    """
    Returns (risk_level, [matched_signals]) for a text chunk.
    """
    lower = text.lower()
    signals: List[str] = []
    risk = "none"

    for kw in HIGH_RISK_KEYWORDS:
        if kw in lower:
            signals.append(f"'{kw}' detected in document")
            risk = "high"

    for kw in MEDIUM_RISK_KEYWORDS:
        if kw in lower and risk != "high":
            signals.append(f"'{kw}' indicator found")
            risk = "medium"

    return risk, signals


def _extract_equipment_from_text(text: str) -> List[str]:
    return list({m.group(0).upper() for m in _EQUIP_RE.finditer(text)})


class RiskAssessmentService:

    @staticmethod
    def assess(
        chunks: List[Dict[str, Any]],
        graph_entities: List[Dict[str, Any]],
        query: str = "",
    ) -> Dict[str, Any]:
        """
        Assess operational risk from retrieved chunks.

        Returns:
          {
            "risk_level": "high" | "medium" | "low" | "none",
            "risk_signals": [...],
            "failure_patterns": [...]
          }
        """
        overall_risk = "none"
        all_signals: List[str] = []

        # Equipment → list of doc names where a risk keyword was found
        equipment_failures: Dict[str, List[str]] = defaultdict(list)

        for chunk in chunks:
            text = chunk.get("text", "")
            doc_title = chunk.get("title", "Unknown Document")

            chunk_risk, signals = _find_risk_keywords(text)

            # Escalate overall risk level
            if chunk_risk == "high" and overall_risk != "high":
                overall_risk = "high"
            elif chunk_risk == "medium" and overall_risk == "none":
                overall_risk = "medium"

            # De-duplicate signals (limit to 4 unique)
            for sig in signals:
                if sig not in all_signals and len(all_signals) < 6:
                    all_signals.append(sig)

            # Equipment failure pattern tracking
            if chunk_risk in ("high", "medium"):
                equipment_tags = _extract_equipment_from_text(text)
                for tag in equipment_tags:
                    if doc_title not in equipment_failures[tag]:
                        equipment_failures[tag].append(doc_title)

        # ── Build failure patterns for equipment seen in ≥2 documents ─────────
        failure_patterns: List[Dict[str, Any]] = []
        for equipment_tag, doc_names in equipment_failures.items():
            if len(doc_names) >= 2:
                failure_patterns.append({
                    "equipment": equipment_tag,
                    "pattern": f"Recurring issue — found in {len(doc_names)} documents",
                    "occurrences": len(doc_names),
                    "source_documents": doc_names[:4],
                })

        # ── If no doc-based risk but query suggests risk context ──────────────
        if overall_risk == "none" and not failure_patterns:
            q_lower = query.lower()
            if any(kw in q_lower for kw in ["fail", "break", "fault", "error", "problem", "issue", "risk"]):
                overall_risk = "low"
                all_signals.append("Query contains risk-related keywords — monitoring recommended")

        # Downgrade to "low" if only signals came from query (not from documents)
        if overall_risk == "none" and not all_signals:
            pass  # keep none

        return {
            "risk_level":       overall_risk,
            "risk_signals":     all_signals,
            "failure_patterns": failure_patterns,
        }

    @staticmethod
    def detect_compliance_signals(
        chunks: List[Dict[str, Any]],
        company_profile: Dict[str, Any] = None,
    ) -> List[Dict[str, Any]]:
        """
        Detects which regulatory/quality standards are present or missing
        across retrieved chunks and the company profile.

        Returns: [{"standard": "...", "status": "present"|"missing", "note": "..."}]
        """
        STANDARDS_TO_CHECK = [
            ("ISO 9001",    ["iso 9001", "iso9001"]),
            ("ISO 14001",   ["iso 14001", "iso14001"]),
            ("ISO 45001",   ["iso 45001", "iso45001"]),
            ("OISD",        ["oisd"]),
            ("PESO",        ["peso"]),
            ("Factory Act", ["factory act", "factories act"]),
            ("HAZOP",       ["hazop", "hazard and operability"]),
            ("LOTO",        ["loto", "lockout", "tagout"]),
        ]

        # Build combined text from all chunks
        all_text = " ".join(c.get("text", "").lower() for c in chunks)

        # Also check company profile standards list
        profile_standards_raw = []
        if company_profile:
            profile_standards_raw = [s.lower() for s in company_profile.get("standards", [])]

        signals: List[Dict[str, Any]] = []
        for standard_name, keywords in STANDARDS_TO_CHECK:
            found_in_docs = any(kw in all_text for kw in keywords)
            found_in_profile = any(kw in " ".join(profile_standards_raw) for kw in keywords)

            if found_in_docs or found_in_profile:
                source = "uploaded documents" if found_in_docs else "company profile"
                signals.append({
                    "standard": standard_name,
                    "status":   "present",
                    "note":     f"Referenced in {source}",
                })
            else:
                # Only report missing standards that are relevant to the context
                # (Don't flood with every possible standard)
                pass

        # Report critical missing standards if profile indicates this industry
        if company_profile:
            industry = (company_profile.get("industry") or "").lower()
            if "oil" in industry or "gas" in industry or "petroleum" in industry:
                for std_name, keywords in [("OISD", ["oisd"]), ("PESO", ["peso"])]:
                    if not any(s["standard"] == std_name for s in signals):
                        signals.append({
                            "standard": std_name,
                            "status":   "missing",
                            "note":     "No documentation found — required for Oil & Gas industry",
                        })
            if "manufactur" in industry:
                if not any(s["standard"] == "ISO 9001" for s in signals):
                    signals.append({
                        "standard": "ISO 9001",
                        "status":   "missing",
                        "note":     "No ISO 9001 documentation uploaded",
                    })

        return signals[:6]   # Cap at 6
