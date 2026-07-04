"""
ConfidenceEngine
=================
Sprint 9 — Industrial Intelligence Copilot

Rule-based confidence scoring (0–98).
Derived entirely from retrieval quality signals — no LLM call required.

Formula:
  base  = average cosine similarity of top chunks × 100
  + 8   if ≥ 3 distinct source documents
  + 5   if interview knowledge matched
  + 5   if knowledge graph entity matched
  − 20  if < 2 chunks found (insufficient evidence)
  − 10  if all chunks score < 0.60 (weak evidence)
  clamp 5 – 98
"""

import logging
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


class ConfidenceEngine:

    @staticmethod
    def score(
        chunks: List[Dict[str, Any]],
        interview_answers: List[Dict[str, Any]],
        graph_entities: List[Dict[str, Any]],
        knowledge_missing: bool = False,
    ) -> int:
        """
        Returns an integer confidence score (0–98).
        """
        if knowledge_missing or not chunks:
            return 0

        # Base: average similarity × 100
        scores = [float(c.get("score", 0.0)) for c in chunks if c.get("score")]
        if not scores:
            return 10

        avg_score = sum(scores) / len(scores)
        confidence = avg_score * 100

        # Bonus: multiple source documents
        distinct_docs = len({c.get("document_id") for c in chunks})
        if distinct_docs >= 3:
            confidence += 8
        elif distinct_docs >= 2:
            confidence += 4

        # Bonus: interview knowledge
        if interview_answers:
            confidence += 5

        # Bonus: graph entity match
        if graph_entities:
            confidence += 5

        # Penalty: not enough evidence
        if len(chunks) < 2:
            confidence -= 20

        # Penalty: all chunks are weak
        if all(float(c.get("score", 0)) < 0.60 for c in chunks):
            confidence -= 10

        # Clamp and return
        return max(5, min(98, int(confidence)))
