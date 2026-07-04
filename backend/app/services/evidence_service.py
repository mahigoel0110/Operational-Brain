"""
EvidenceService
================
Sprint 9 — Industrial Intelligence Copilot

Converts raw retrieval chunks into structured citation objects
with star ratings (1–5) derived from cosine similarity scores.
"""

import logging
from typing import Any, Dict, List

logger = logging.getLogger(__name__)

# Score → star rating bands
STAR_BANDS = [
    (0.85, 5),
    (0.75, 4),
    (0.65, 3),
    (0.55, 2),
    (0.00, 1),
]


def _score_to_stars(score: float) -> int:
    for threshold, stars in STAR_BANDS:
        if score >= threshold:
            return stars
    return 1


def _truncate_excerpt(text: str, max_chars: int = 200) -> str:
    """Return a clean, truncated excerpt."""
    text = text.strip().replace("\n", " ")
    if len(text) <= max_chars:
        return text
    return text[:max_chars].rsplit(" ", 1)[0] + "…"


class EvidenceService:

    @staticmethod
    def build_citations(
        chunks: List[Dict[str, Any]],
        interview_answers: List[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Converts retrieved chunks and interview answers into citation objects.

        Returns a list sorted by descending score (highest confidence first).
        """
        citations: List[Dict[str, Any]] = []
        seen_chunks: set = set()

        # ── Document citations (from Qdrant) ──────────────────────────────────
        for chunk in chunks:
            chunk_id = str(chunk.get("id", ""))
            if chunk_id in seen_chunks:
                continue
            seen_chunks.add(chunk_id)

            score = float(chunk.get("score", 0.0))
            stars = _score_to_stars(score)
            text = chunk.get("text", "")

            citations.append({
                "document_id":  chunk.get("document_id", ""),
                "title":        chunk.get("title", "Untitled Document"),
                "page_number":  chunk.get("page_number", 1),
                "section":      chunk.get("department", ""),
                "chunk_id":     chunk_id,
                "excerpt":      _truncate_excerpt(text),
                "score":        round(score, 4),
                "stars":        stars,
                "source_type":  "document",
            })

        # ── Interview citations ────────────────────────────────────────────────
        if interview_answers:
            for ans in interview_answers[:3]:   # max 3 interview citations
                citations.append({
                    "document_id":  "",
                    "title":        f"Interview — {ans.get('department', 'General')}",
                    "page_number":  0,
                    "section":      ans.get("department", ""),
                    "chunk_id":     ans.get("answer_id", ""),
                    "excerpt":      _truncate_excerpt(f"Q: {ans.get('question','')} A: {ans.get('answer','')}"),
                    "score":        0.70,   # interviews are moderately reliable
                    "stars":        3,
                    "source_type":  "interview",
                })

        # Sort by score descending
        citations.sort(key=lambda c: c["score"], reverse=True)
        return citations

    @staticmethod
    def build_related_metadata(
        chunks: List[Dict[str, Any]],
        graph_entities: List[Dict[str, Any]],
        company_profile: Dict[str, Any] = None,
    ) -> Dict[str, List[str]]:
        """
        Builds the 'related' metadata block:
        equipment, departments, standards — from chunks + graph entities.
        """
        equipment: set = set()
        departments: set = set()
        standards: set = set()

        # From graph entities (highest quality)
        for entity_doc in graph_entities:
            for entity in entity_doc.get("entities", []):
                if entity["type"] == "equipment":
                    equipment.add(entity["value"])
                elif entity["type"] == "standard":
                    standards.add(entity["value"])
                elif entity["type"] == "department":
                    departments.add(entity["value"])
            dept = entity_doc.get("department", "")
            if dept:
                departments.add(dept)

        # From chunk payloads
        for chunk in chunks:
            dept = chunk.get("department", "")
            if dept and dept != "General":
                departments.add(dept)

        # From company profile
        if company_profile:
            for std in company_profile.get("standards", []):
                if std:
                    standards.add(std)

        return {
            "equipment":   sorted(list(equipment))[:6],
            "departments": sorted(list(departments))[:5],
            "standards":   sorted(list(standards))[:4],
        }
