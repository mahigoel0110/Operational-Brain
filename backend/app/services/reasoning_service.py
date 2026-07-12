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
MAX_CHUNK_CHARS = 2500
MAX_INTERVIEW_CHARS = 800

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


_SYSTEM_PROMPT = """You are an Enterprise Industrial Intelligence Copilot (OperationalBrain).
Your role: Act as a senior plant engineer who reads multiple manuals, SOPs, maintenance documents, and inspection reports to reason over them and produce a highly professional engineering answer.

RULES:
1. Answer ONLY from the provided knowledge context (documents, interviews, graph). Do NOT hallucinate.
2. Cross-Document Intelligence: Combine information from multiple documents. Compare them automatically.
3. Conflict Detection: If two documents disagree (e.g., Manual says X, SOP says Y), highlight the conflict and recommend engineering verification.
4. Response Style: Write in natural English. DO NOT copy/paste raw chunks. Never just paste "Source: X". Explain professionally.
5. Answer Generator Structure: Your `answer` string MUST be formatted in Markdown and MUST follow this EXACT structure:

### Executive Summary
[A short human-readable explanation of the overall answer.]

### Findings
[Synthesized explanation of what the retrieved documents say. Compare and combine information from multiple sources.]

### Root Cause
[If possible, determine likely cause, possible cause, or unknown cause based on evidence. Mention common industrial causes if supported by text.]

### Recommended Actions
[Step-by-step recommendations. Prioritize Immediate actions, Preventive actions, Long-term improvements. Back every recommendation with documents.]

### Safety Notes
[Mention LOTO, PPE, Isolation, Pressure, Temperature, Hazards if relevant.]

### Supporting Evidence
[List every supporting document tracing back to your findings.
Example:
Source: Pump Manual
Page 18
Section 5]

### Confidence
[Very High, High, Medium, Low. Explain why. Example: "High confidence because 4 independent documents mention the same procedure."]

6. If knowledge is missing to fully answer the query, structure the answer based on what you know, but explicitly mention Knowledge Gaps under Findings, and set `knowledge_missing: true`.

RESPONSE FORMAT — return ONLY valid JSON, no markdown fences:
{
  "answer": "The fully structured Markdown response containing ALL the headers specified above.",
  "reasoning": "I combined [list sources] to produce this answer because [explain synthesis, including any risk assessment or maintenance intelligence].",
  "knowledge_missing": false
}
"""


class ReasoningService:

    @staticmethod
    async def generate(
        query: str,
        knowledge_context: Dict[str, Any],
        conversation_history: Optional[List[Dict[str, str]]] = None,
    ) -> Dict[str, Any]:
        """
        Builds the full prompt and calls the LLM.
        Returns {"answer": str, "reasoning": str, "knowledge_missing": bool}
        """
        chunks = knowledge_context.get("document_chunks", [])
        interview_answers = knowledge_context.get("interview_answers", [])
        company_profile = knowledge_context.get("company_profile", None)
        graph_summary = knowledge_context.get("graph_summary", "")

        # If no chunks at all, skip LLM and return fallback directly
        if not chunks and not interview_answers and not graph_summary:
            return FALLBACK_RESPONSE

        # Build context sections
        doc_section = _format_chunks(chunks)
        interview_section = _format_interview(interview_answers)
        profile_section = _format_profile(company_profile)

        # Build the final prompt with explicit sections
        prompt_parts = []
        
        if doc_section and doc_section != "No document knowledge available.":
            prompt_parts.append("===========================\nDOCUMENT CONTEXT\n===========================\n" + doc_section)
            
        if graph_summary:
            prompt_parts.append("===========================\nKNOWLEDGE GRAPH CONTEXT\n===========================\n" + graph_summary)
            
        if interview_section and interview_section != "No interview knowledge available.":
            prompt_parts.append("===========================\nINTERVIEW KNOWLEDGE\n===========================\n" + interview_section)
            
        if profile_section and profile_section != "Company profile not available.":
            prompt_parts.append("===========================\nCOMPANY PROFILE\n===========================\n" + profile_section)

        prompt_parts.append(f"===========================\nQUESTION\n===========================\n{query}")
        
        prompt_parts.append("===========================\nINSTRUCTIONS\n===========================\n"
                            "Use both the document context and the knowledge graph (if provided).\n"
                            "If they disagree, prefer the document context.\n"
                            "If the graph adds missing relationships, use them to provide a complete answer.\n"
                            "Do not invent facts.\n"
                            "Return ONLY a JSON object as specified.")

        user_prompt = "\n\n".join(prompt_parts)

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
