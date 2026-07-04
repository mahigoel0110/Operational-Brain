"""
QueryExpansionService
=====================
Sprint 9 — Industrial Intelligence Copilot

Pure-Python industrial synonym and abbreviation expansion.
Zero cost. Zero API calls.

Maps common industrial abbreviations to their full forms,
and adds industry-specific synonyms to improve retrieval.
"""

import re
import logging
from typing import List, Optional

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# UNIVERSAL INDUSTRIAL ABBREVIATIONS
# ─────────────────────────────────────────────────────────────────────────────

ABBREVIATIONS: dict[str, str] = {
    # Equipment patterns (handled via regex separately)
    "PM":       "Preventive Maintenance",
    "CM":       "Corrective Maintenance",
    "CBM":      "Condition Based Maintenance",
    "SOP":      "Standard Operating Procedure",
    "RCA":      "Root Cause Analysis",
    "HSE":      "Health Safety Environment",
    "PPE":      "Personal Protective Equipment",
    "CMMS":     "Computerized Maintenance Management System",
    "OEM":      "Original Equipment Manufacturer",
    "MTBF":     "Mean Time Between Failures",
    "MTTR":     "Mean Time To Repair",
    "KPI":      "Key Performance Indicator",
    "WO":       "Work Order",
    "WIP":      "Work In Progress",
    "BOM":      "Bill Of Materials",
    "MOC":      "Management of Change",
    "LOTO":     "Lockout Tagout",
    "PTW":      "Permit To Work",
    "ISO":      "ISO Standard",
    "OISD":     "Oil Industry Safety Directorate",
    "PESO":     "Petroleum and Explosives Safety Organisation",
    "QMS":      "Quality Management System",
    "ERP":      "Enterprise Resource Planning",
    "MRP":      "Material Requirements Planning",
    "TBM":      "Time Based Maintenance",
    "TPM":      "Total Productive Maintenance",
    "OEE":      "Overall Equipment Effectiveness",
    "FMEA":     "Failure Mode and Effects Analysis",
    "HAZOP":    "Hazard and Operability Study",
    "MSDS":     "Material Safety Data Sheet",
    "SDS":      "Safety Data Sheet",
    "P&ID":     "Piping and Instrumentation Diagram",
    "PFD":      "Process Flow Diagram",
    "SIL":      "Safety Integrity Level",
    "MOC":      "Management of Change",
}

# ─────────────────────────────────────────────────────────────────────────────
# INDUSTRY-SPECIFIC SYNONYM EXPANSIONS
# ─────────────────────────────────────────────────────────────────────────────

INDUSTRY_SYNONYMS: dict[str, list[str]] = {
    "Manufacturing": [
        "production", "assembly", "quality control", "inspection",
        "machining", "fabrication", "throughput", "yield"
    ],
    "Oil & Gas": [
        "upstream", "downstream", "wellhead", "pipeline", "refinery",
        "separator", "compressor station", "SCADA", "flare", "hydrocarbon"
    ],
    "Pharmaceutical": [
        "GMP", "batch record", "validation", "cleanroom", "API",
        "bioburden", "sterilization", "cGMP", "deviation", "CAPA"
    ],
    "Healthcare": [
        "clinical protocol", "patient safety", "medical device",
        "biomedical", "sterilization", "infection control"
    ],
    "Power & Utilities": [
        "grid", "transformer", "substation", "turbine", "boiler",
        "switchgear", "protection relay", "load dispatch"
    ],
}

# ─────────────────────────────────────────────────────────────────────────────
# EQUIPMENT TAG NORMALIZATION
# e.g. "P101" → "Pump P-101", "V22" → "Valve V-22"
# ─────────────────────────────────────────────────────────────────────────────

EQUIPMENT_PREFIXES = {
    "P":  "Pump",
    "C":  "Compressor",
    "V":  "Valve",
    "T":  "Tank",
    "E":  "Heat Exchanger",
    "R":  "Reactor",
    "K":  "Boiler",
    "G":  "Generator",
    "M":  "Motor",
    "F":  "Filter",
    "HX": "Heat Exchanger",
    "TK": "Tank",
}

_EQUIP_RE = re.compile(
    r'\b(HX|TK|[PCVTERKGMF])-?(\d{2,4})\b',
    re.IGNORECASE
)


def _normalize_equipment_tags(text: str) -> str:
    """Expand equipment tags: P101 → Pump P-101, V-22 → Valve V-22."""
    def replace(m: re.Match) -> str:
        prefix = m.group(1).upper()
        number = m.group(2)
        tag = f"{prefix}-{number}"
        full = EQUIPMENT_PREFIXES.get(prefix, "")
        if full:
            return f"{full} {tag}"
        return tag
    return _EQUIP_RE.sub(replace, text)


class QueryExpansionService:

    @staticmethod
    def expand(query: str, industry: Optional[str] = None) -> str:
        """
        Expands a query with industrial synonyms and normalized equipment tags.

        Returns the expanded query string (original + expansions appended).
        This enriches the embedding without modifying the user's visible query.
        """
        expanded = query.strip()

        # 1. Normalize equipment tags (P101 → Pump P-101)
        expanded = _normalize_equipment_tags(expanded)

        # 2. Expand known abbreviations (whole-word only)
        tokens: List[str] = []
        for word in expanded.split():
            clean = word.strip(".,;:?!()[]")
            upper = clean.upper()
            if upper in ABBREVIATIONS:
                tokens.append(f"{word} ({ABBREVIATIONS[upper]})")
            else:
                tokens.append(word)
        expanded = " ".join(tokens)

        # 3. Append industry context if available
        if industry and industry in INDUSTRY_SYNONYMS:
            # Only add the top 3 most relevant synonyms to avoid noise
            synonyms = INDUSTRY_SYNONYMS[industry][:3]
            context = " ".join(synonyms)
            expanded = f"{expanded} {context}"

        logger.debug(f"Query expanded: '{query}' → '{expanded}'")
        return expanded

    @staticmethod
    def extract_equipment_mentions(query: str) -> List[str]:
        """Extract all equipment tags mentioned in a query."""
        matches = _EQUIP_RE.findall(query)
        return [f"{m[0].upper()}-{m[1]}" for m in matches]
