"""
CopilotOrchestrator
====================
Sprint 9 — Industrial Intelligence Copilot

Top-level coordinator that chains all sub-services together:

  Query
    ↓ QueryExpansionService
    ↓ KnowledgeRetrievalService  (Qdrant + Graph + Interview + Profile)
    ↓ ReasoningService            (LLM call)
    ↓ EvidenceService             (citations + star ratings)
    ↓ RiskAssessmentService       (failure patterns + compliance signals)
    ↓ ActionRecommendationService (next actions)
    ↓ ConfidenceEngine            (score 0–98)
    ↓ SuggestionEngine            (follow-up questions)
    ↓ CopilotResponse
"""

import logging
import re
import uuid
from datetime import datetime, UTC
from typing import Any, Dict, List, Optional

from app.models.copilot import (
    CopilotSession, CopilotMessage,
    CitationRecord, FailurePattern, ComplianceSignal, SourcesConsulted
)
from app.models.company_profile import CompanyProfile
from app.services.query_expansion_service import QueryExpansionService
from app.services.knowledge_retrieval_service import KnowledgeRetrievalService
from app.services.reasoning_service import ReasoningService
from app.services.evidence_service import EvidenceService
from app.services.risk_assessment_service import RiskAssessmentService
from app.services.action_recommendation_service import ActionRecommendationService
from app.services.confidence_engine import ConfidenceEngine
from app.services.suggestion_engine import SuggestionEngine

logger = logging.getLogger(__name__)

_EQUIP_RE = re.compile(r'\b([A-Z]{1,2}-?\d{2,4})\b', re.IGNORECASE)


class CopilotOrchestrator:

    @staticmethod
    async def answer(
        workspace_id: str,
        user_id: str,
        message: str,
        session_id: Optional[str] = None,
        document_context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Full reasoning pipeline. Returns the complete structured response dict.
        """
        import time
        pipeline_start = time.time()

        # ── 0. Load or create session ────────────────────────────────────────
        session: Optional[CopilotSession] = None
        conversation_history: List[Dict[str, str]] = []

        if session_id:
            try:
                session = await CopilotSession.get(session_id)
            except Exception:
                session = None

        if session is None:
            session = CopilotSession(
                workspace_id=workspace_id,
                user_id=user_id,
                messages=[],
            )
            await session.insert()

        # Build short history for LLM context
        for msg in session.messages[-6:]:
            conversation_history.append({
                "role": msg.role,
                "content": msg.content[:400],
            })

        # ── 1. Query expansion ───────────────────────────────────────────────
        # Get company profile for industry context
        industry: Optional[str] = None
        try:
            profile_obj = await CompanyProfile.find_one(
                CompanyProfile.workspace_id == workspace_id
            )
            if profile_obj:
                industry = profile_obj.industry
        except Exception:
            pass

        expanded_query = QueryExpansionService.expand(message, industry)
        equipment_mentioned = QueryExpansionService.extract_equipment_mentions(message)

        # ── 2. Knowledge retrieval ───────────────────────────────────────────
        doc_ctx_id = document_context.get("document_id") if document_context else None
        context = await KnowledgeRetrievalService.retrieve(
            workspace_id=workspace_id,
            expanded_query=expanded_query,
            original_query=message,
            document_context_id=doc_ctx_id,
        )

        chunks           = context["chunks"]
        interview_answers = context["interview_answers"]
        company_profile   = context["company_profile"]
        graph_entities    = context["graph_entities"]
        retrieval_stats   = context["stats"]

        # If document context provides an excerpt, prepend it as a synthetic chunk
        if document_context and document_context.get("excerpt"):
            synthetic = {
                "id":          "ctx_excerpt",
                "score":       0.95,
                "text":        document_context["excerpt"],
                "document_id": doc_ctx_id or "",
                "page_number": 1,
                "title":       document_context.get("document_name", "Selected Document"),
                "department":  "",
            }
            chunks = [synthetic] + chunks

        # ── 3. LLM reasoning ─────────────────────────────────────────────────
        reasoning_result = await ReasoningService.generate(
            query=message,
            chunks=chunks,
            interview_answers=interview_answers,
            company_profile=company_profile,
            conversation_history=conversation_history,
        )

        answer          = reasoning_result["answer"]
        reasoning_text  = reasoning_result["reasoning"]
        knowledge_missing = reasoning_result["knowledge_missing"]

        missing_explanation: Optional[str] = None
        if knowledge_missing:
            missing_explanation = reasoning_text

        # ── 4. Citations & related metadata ──────────────────────────────────
        citations_raw = EvidenceService.build_citations(chunks, interview_answers)
        related = EvidenceService.build_related_metadata(
            chunks, graph_entities, company_profile
        )

        # ── 5. Risk assessment ───────────────────────────────────────────────
        risk_result = RiskAssessmentService.assess(chunks, graph_entities, message)
        risk_level      = risk_result["risk_level"]
        risk_signals    = risk_result["risk_signals"]
        failure_patterns_raw = risk_result["failure_patterns"]

        # Compliance signals
        compliance_raw = RiskAssessmentService.detect_compliance_signals(
            chunks, company_profile
        )

        # ── 6. Actions ───────────────────────────────────────────────────────
        recommended_actions = ActionRecommendationService.recommend(
            query=message,
            risk_level=risk_level,
            knowledge_missing=knowledge_missing,
            failure_patterns=failure_patterns_raw,
            equipment_mentioned=equipment_mentioned or list(related.get("equipment", [])),
        )

        # ── 7. Confidence ────────────────────────────────────────────────────
        confidence = ConfidenceEngine.score(
            chunks=chunks,
            interview_answers=interview_answers,
            graph_entities=graph_entities,
            knowledge_missing=knowledge_missing,
        )

        # ── 8. Suggestions ───────────────────────────────────────────────────
        suggestions = SuggestionEngine.suggest(
            query=message,
            industry=industry,
            equipment_mentioned=equipment_mentioned or list(related.get("equipment", [])),
        )

        # ── 9. Timing ────────────────────────────────────────────────────────
        elapsed_ms = int((time.time() - pipeline_start) * 1000)
        retrieval_stats["response_time_ms"] = elapsed_ms

        # ── 10. Persist to session ───────────────────────────────────────────
        # User message
        user_msg = CopilotMessage(
            role="user",
            content=message,
            created_at=datetime.now(UTC),
        )

        # Build typed citation records
        citation_records = [
            CitationRecord(
                document_id=c["document_id"],
                title=c["title"],
                page_number=c["page_number"],
                section=c.get("section", ""),
                chunk_id=c["chunk_id"],
                excerpt=c["excerpt"],
                score=c["score"],
                stars=c["stars"],
                source_type=c["source_type"],
            )
            for c in citations_raw
        ]

        failure_pattern_records = [
            FailurePattern(
                equipment=fp["equipment"],
                pattern=fp["pattern"],
                occurrences=fp["occurrences"],
                source_documents=fp["source_documents"],
            )
            for fp in failure_patterns_raw
        ]

        compliance_records = [
            ComplianceSignal(
                standard=cs["standard"],
                status=cs["status"],
                note=cs["note"],
            )
            for cs in compliance_raw
        ]

        sources_consulted = SourcesConsulted(
            documents_searched=retrieval_stats["documents_searched"],
            chunks_retrieved=retrieval_stats["chunks_retrieved"],
            interview_answers_checked=retrieval_stats["interview_answers_checked"],
            graph_entities_matched=retrieval_stats["graph_entities_matched"],
            company_profile_used=retrieval_stats["company_profile_used"],
            response_time_ms=elapsed_ms,
        )

        assistant_msg = CopilotMessage(
            role="assistant",
            content=answer,
            reasoning=reasoning_text,
            confidence=confidence,
            risk_level=risk_level,
            knowledge_missing=knowledge_missing,
            missing_explanation=missing_explanation,
            citations=citation_records,
            failure_patterns=failure_pattern_records,
            risk_signals=risk_signals,
            recommended_actions=recommended_actions,
            compliance_signals=compliance_records,
            sources_consulted=sources_consulted,
            related=related,
            suggestions=suggestions,
            created_at=datetime.now(UTC),
        )

        session.messages.append(user_msg)
        session.messages.append(assistant_msg)
        session.updated_at = datetime.now(UTC)
        await session.save()

        # ── 11. Build response dict ──────────────────────────────────────────
        return {
            "answer":               answer,
            "reasoning":            reasoning_text,
            "confidence":           confidence,
            "risk_level":           risk_level,
            "knowledge_missing":    knowledge_missing,
            "missing_explanation":  missing_explanation,
            "citations":            citations_raw,
            "failure_patterns":     failure_patterns_raw,
            "risk_signals":         risk_signals,
            "recommended_actions":  recommended_actions,
            "compliance_signals":   compliance_raw,
            "sources_consulted":    retrieval_stats,
            "related":              related,
            "suggestions":          suggestions,
            "session_id":           str(session.id),
        }
