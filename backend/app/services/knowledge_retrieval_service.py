"""
KnowledgeRetrievalService
==========================
Sprint 9 — Industrial Intelligence Copilot

Searches all knowledge sources in parallel:
  1. Qdrant vector store (document chunks)
  2. Knowledge graph traversal (via extracted_metadata entity matching)
  3. Interview answers (MongoDB keyword matching)
  4. Company profile (MongoDB lookup)

Returns a unified KnowledgeContext dict.
"""

import logging
import re
from typing import Any, Dict, List, Optional

from app.models.document import DocumentModel
from app.models.interview import InterviewAnswer, InterviewSession
from app.models.company_profile import CompanyProfile
from app.services.embedding_service import EmbeddingService
from app.services.vector_store import VectorStoreService
from app.core.config import settings

logger = logging.getLogger(__name__)

# How many chunks to retrieve from Qdrant
CHUNK_LIMIT = 8

# Minimum score to include a chunk
MIN_SCORE = 0.30


class KnowledgeRetrievalService:

    @staticmethod
    async def retrieve(
        workspace_id: str,
        expanded_query: str,
        original_query: str,
        document_context_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Searches all knowledge sources and returns a structured KnowledgeContext.

        Args:
            workspace_id:         Target workspace
            expanded_query:       Query after abbreviation/synonym expansion
            original_query:       Original user query (for keyword matching)
            document_context_id:  If set, boost chunks from this document
        """
        import time
        start = time.time()

        # ── 1. Semantic search (Qdrant) ──────────────────────────────────────
        chunks: List[Dict[str, Any]] = []
        documents_searched = 0
        try:
            embeddings = await EmbeddingService.get_embeddings([expanded_query])
            if embeddings:
                collection = settings.QDRANT_COLLECTION_NAME or "documents_general"
                raw_results = await VectorStoreService.search_workspace(
                    collection_name=collection,
                    workspace_id=workspace_id,
                    query_vector=embeddings[0],
                    limit=CHUNK_LIMIT
                )
                # Filter by minimum score
                chunks = [r for r in raw_results if r.get("score", 0) >= MIN_SCORE]

                # If document context given, boost those chunks to the front
                if document_context_id:
                    ctx_chunks = [c for c in chunks if c.get("document_id") == document_context_id]
                    other_chunks = [c for c in chunks if c.get("document_id") != document_context_id]
                    chunks = ctx_chunks + other_chunks

                # Count unique documents searched
                doc_ids = {c.get("document_id") for c in chunks}
                documents_searched = len(doc_ids)

        except Exception as e:
            logger.error(f"Vector search failed: {e}")

        # ── 2. Knowledge Graph traversal via extracted_metadata ───────────────
        graph_entities: List[Dict[str, Any]] = []
        try:
            # Extract equipment tags from query (e.g. "P-101", "V-22")
            tag_pattern = re.compile(r'\b([A-Z]{1,2}-?\d{2,4})\b', re.IGNORECASE)
            query_tags = [m.group(0).upper() for m in tag_pattern.finditer(original_query)]

            # Also extract nouns that might match department/standards
            query_lower = original_query.lower()

            # Find documents whose metadata mentions these entities
            all_docs = await DocumentModel.find(
                DocumentModel.workspace_id == workspace_id
            ).to_list()

            for doc in all_docs:
                if not doc.extracted_metadata:
                    continue
                meta = doc.extracted_metadata
                matched_entities = []

                # Check machines / equipment
                machines: List[str] = meta.get("machines", [])
                for tag in query_tags:
                    for machine in machines:
                        if tag.replace("-", "") in machine.replace("-", "").upper():
                            matched_entities.append({"type": "equipment", "value": machine})

                # Check standards
                standards: List[str] = meta.get("standards", []) or []
                for std in standards:
                    if std.lower() in query_lower:
                        matched_entities.append({"type": "standard", "value": std})

                # Check department match
                dept: str = doc.department or meta.get("department", "")
                if dept and dept.lower() in query_lower:
                    matched_entities.append({"type": "department", "value": dept})

                if matched_entities:
                    graph_entities.append({
                        "document_id": str(doc.id),
                        "document_name": doc.name,
                        "entities": matched_entities,
                        "department": dept,
                    })

        except Exception as e:
            logger.error(f"Knowledge graph traversal failed: {e}")

        # ── 3. Interview answers (keyword matching) ──────────────────────────
        interview_answers: List[Dict[str, Any]] = []
        try:
            # Find all answers for this workspace's sessions
            sessions = await InterviewSession.find(
                InterviewSession.workspace_id == workspace_id
            ).to_list()
            session_ids = [str(s.id) for s in sessions]

            if session_ids:
                all_answers = await InterviewAnswer.find(
                    {"session_id": {"$in": session_ids}}
                ).to_list()

                # Score answers by keyword overlap with query
                query_words = set(re.findall(r'\w+', query_lower))
                scored_answers = []
                for ans in all_answers:
                    text = (ans.question_text + " " + ans.answer).lower()
                    answer_words = set(re.findall(r'\w+', text))
                    # Remove common stop words
                    overlap = query_words & answer_words - {
                        "the","a","an","is","are","was","were","what","how","why",
                        "when","where","which","do","does","did","to","of","in","for"
                    }
                    if len(overlap) >= 2:
                        scored_answers.append({
                            "score": len(overlap),
                            "question": ans.question_text,
                            "answer": ans.answer,
                            "department": ans.department,
                            "answer_id": str(ans.id),
                        })

                # Sort by overlap score, take top 5
                scored_answers.sort(key=lambda x: x["score"], reverse=True)
                interview_answers = scored_answers[:5]

        except Exception as e:
            logger.error(f"Interview answer retrieval failed: {e}")

        # ── 4. Company profile ───────────────────────────────────────────────
        company_profile: Optional[Dict[str, Any]] = None
        try:
            profile = await CompanyProfile.find_one(
                CompanyProfile.workspace_id == workspace_id
            )
            if profile:
                company_profile = {
                    "industry": profile.industry or "",
                    "company_name": profile.company_name or "",
                    "departments": profile.departments or [],
                    "machines": profile.machines or [],
                    "standards": profile.standards or [],
                    "processes": profile.processes or [],
                    "erp": profile.erp or "",
                    "core_business": profile.core_business or "",
                    "department_summaries": profile.department_summaries or {},
                }
        except Exception as e:
            logger.error(f"Company profile retrieval failed: {e}")

        elapsed_ms = int((time.time() - start) * 1000)

        return {
            "chunks": chunks,
            "interview_answers": interview_answers,
            "company_profile": company_profile,
            "graph_entities": graph_entities,
            "stats": {
                "documents_searched": documents_searched,
                "chunks_retrieved": len(chunks),
                "interview_answers_checked": len(interview_answers),
                "graph_entities_matched": len(graph_entities),
                "company_profile_used": company_profile is not None,
                "response_time_ms": elapsed_ms,
            },
        }
