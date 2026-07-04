"""
ReasoningService
=================
Sprint 9 — Industrial Intelligence Copilot

Builds the industrial-grade system prompt and calls the LLM.
Returns a structured dict with answer, reasoning, and knowledge_missing flag.

Falls back gracefully when no API key is configured.
"""

import json
import logging
import re
from typing import Any, Dict, List, Optional

from app.services.llm_service import LLMService

logger = logging.getLogger(__name__)

# Characters of chunk text to include per source (keep context window sane)
MAX_CHUNK_CHARS = 600
MAX_INTERVIEW_CHARS = 400

FALLBACK_RESPONSE = {
    "answer": (
        "I currently do not have enough indexed knowledge to answer this accurately. "
        "No relevant documents were found in the vector store for this workspace."
    ),
    "reasoning": "Retrieval returned no relevant chunks — knowledge base may be empty or the query topic is not covered by uploaded documents.",
    "knowledge_missing": True,
}


def _format_chunks(chunks: List[Dict[str, Any]]) -> str:
    if not chunks:
        return "No document knowledge available."
    lines = []
    for i, chunk in enumerate(chunks[:6], 1):
        title = chunk.get("title", "Unknown")
        page = chunk.get("page_number", 1)
        score = chunk.get("score", 0)
        text = chunk.get("text", "")[:MAX_CHUNK_CHARS]
        lines.append(f"[Source {i}] {title} (page {page}, relevance {score:.2f}):\n{text}")
    return "\n\n".join(lines)


def _format_interview(answers: List[Dict[str, Any]]) -> str:
    if not answers:
        return "No interview knowledge available."
    lines = []
    for ans in answers[:4]:
        dept = ans.get("department", "General")
        q = ans.get("question", "")[:150]
        a = ans.get("answer", "")[:MAX_INTERVIEW_CHARS]
        lines.append(f"[{dept} Interview] Q: {q}\nA: {a}")
    return "\n\n".join(lines)


def _format_profile(profile: Optional[Dict[str, Any]]) -> str:
    if not profile:
        return "Company profile not available."
    parts = []
    if profile.get("company_name"):
        parts.append(f"Company: {profile['company_name']}")
    if profile.get("industry"):
        parts.append(f"Industry: {profile['industry']}")
    if profile.get("core_business"):
        parts.append(f"Business: {profile['core_business']}")
    if profile.get("departments"):
        parts.append(f"Departments: {', '.join(profile['departments'])}")
    if profile.get("machines"):
        parts.append(f"Key Equipment: {', '.join(profile['machines'][:8])}")
    if profile.get("standards"):
        parts.append(f"Standards: {', '.join(profile['standards'][:6])}")
    return "\n".join(parts) if parts else "Minimal company profile available."


_SYSTEM_PROMPT = """You are OperationalBrain Expert — an Industrial AI Reasoning Agent.

Your role: Answer like the most experienced senior engineer in the organization.
You have access to the company's uploaded documents, interview knowledge, and operational profile.

RULES:
1. Answer ONLY from the provided knowledge context below.
2. If the answer cannot be found in the context, set knowledge_missing to true and explain what is missing.
3. Never hallucinate or invent information not present in the context.
4. Always cite which sources you used in the reasoning field.
5. Use professional engineering language — concise and precise.
6. Detect if the question relates to a failure, risk, or safety concern and flag it.

RESPONSE FORMAT — return ONLY valid JSON, no markdown fences:
{
  "answer": "Direct, professional answer to the question",
  "reasoning": "I combined [list the source documents/interviews used] to produce this answer because [brief explanation of the synthesis]",
  "knowledge_missing": false
}

If knowledge is insufficient:
{
  "answer": "I currently do not have enough knowledge to answer this accurately.",
  "reasoning": "The knowledge base does not contain [what is missing]. Uploading [document type] would allow me to answer this.",
  "knowledge_missing": true
}
"""


class ReasoningService:

    @staticmethod
    async def generate(
        query: str,
        chunks: List[Dict[str, Any]],
        interview_answers: List[Dict[str, Any]],
        company_profile: Optional[Dict[str, Any]],
        conversation_history: Optional[List[Dict[str, str]]] = None,
    ) -> Dict[str, Any]:
        """
        Builds the full prompt and calls the LLM.
        Returns {"answer": str, "reasoning": str, "knowledge_missing": bool}
        """
        # If no chunks at all, skip LLM and return fallback directly
        if not chunks and not interview_answers:
            return FALLBACK_RESPONSE

        # Build context sections
        doc_section = _format_chunks(chunks)
        interview_section = _format_interview(interview_answers)
        profile_section = _format_profile(company_profile)

        user_prompt = (
            f"QUESTION: {query}\n\n"
            f"=== DOCUMENT KNOWLEDGE ===\n{doc_section}\n\n"
            f"=== INTERVIEW KNOWLEDGE ===\n{interview_section}\n\n"
            f"=== COMPANY PROFILE ===\n{profile_section}\n\n"
            "Provide your answer strictly based on the above knowledge. "
            "Return ONLY a JSON object as specified."
        )

        try:
            # Build messages list — include recent conversation context if available
            messages = [{"role": "system", "content": _SYSTEM_PROMPT}]
            if conversation_history:
                # Add last 4 turns for context (don't bloat the window)
                for msg in conversation_history[-4:]:
                    if msg.get("role") in ("user", "assistant") and msg.get("content"):
                        messages.append({"role": msg["role"], "content": msg["content"][:500]})
            messages.append({"role": "user", "content": user_prompt})

            raw = await LLMService.generate_chat(messages, temperature=0.2)

            # Strip any accidental markdown fences
            raw = raw.strip()
            raw = re.sub(r'^```(?:json)?\s*', '', raw)
            raw = re.sub(r'\s*```$', '', raw)

            parsed = json.loads(raw)

            return {
                "answer": parsed.get("answer", "Response generation failed."),
                "reasoning": parsed.get("reasoning", ""),
                "knowledge_missing": bool(parsed.get("knowledge_missing", False)),
            }

        except Exception as e:
            logger.error(f"ReasoningService LLM call failed: {e}")

            # Graceful fallback — answer from first chunk's text
            if chunks:
                best = chunks[0]
                return {
                    "answer": (
                        f"Based on '{best.get('title', 'uploaded documents')}': "
                        f"{best.get('text', '')[:400]}"
                    ),
                    "reasoning": "LLM generation failed — showing the most relevant document excerpt directly.",
                    "knowledge_missing": False,
                }
            return FALLBACK_RESPONSE
