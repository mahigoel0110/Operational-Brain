from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any, List
from datetime import datetime

from app.core.dependencies import get_current_user
from app.models.user import User
from app.schemas.interview import (
    InterviewStartRequest,
    InterviewAnswerRequest,
    InterviewChatRequest,
    InterviewChatResponse,
    RecommendationResponse,
    DepartmentRecommendation,
    RecommendedDocument,
)
from app.services.interview_service import (
    InterviewService,
    QuestionService,
    AnswerService,
    ProgressService,
    RecommendationEngine,
    _SESSION_STATE,
    _get_or_init_session_state,
)
from app.models.interview import InterviewSession, InterviewRecommendation
from app.models.company_profile import CompanyProfile

router = APIRouter()


# ─────────────────────────────────────────────────────────────────────────────
# START / RESUME
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/start")
async def start_interview(
    request: InterviewStartRequest,
    current_user: User = Depends(get_current_user),
):
    session = await InterviewService.start_interview(
        request.workspace_id, str(current_user.id)
    )
    return {
        "session_id": str(session.id),
        "status": session.status,
        "detected_industry": session.detected_industry,
        "department_queue": session.department_queue,
    }


@router.get("/session/{session_id}")
async def get_session(
    session_id: str,
    current_user: User = Depends(get_current_user),
):
    session = await InterviewSession.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


# ─────────────────────────────────────────────────────────────────────────────
# FIRST QUESTION (called when chat starts)
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/first-question/{session_id}")
async def get_first_question(
    session_id: str,
    current_user: User = Depends(get_current_user),
):
    session = await InterviewSession.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    result = await InterviewService.get_first_question(session)
    return result


# ─────────────────────────────────────────────────────────────────────────────
# MAIN CHAT ENDPOINT (core of the interview engine)
# POST /interview/chat
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/chat")
async def interview_chat(
    request: InterviewChatRequest,
    current_user: User = Depends(get_current_user),
):
    """
    Main conversational interview endpoint.
    Receives user message + session context, returns AI next question.
    """
    session = await InterviewSession.get(request.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if session.status == "completed":
        raise HTTPException(status_code=400, detail="Interview already completed")

    # Get current question context from in-memory state
    state = _SESSION_STATE.get(request.session_id)
    if not state:
        state = _get_or_init_session_state(session)

    # Determine context of the question just answered
    idx = state["index"]
    questions = state["questions"]

    # The question that was just answered is at index-1 (we already advanced)
    if state.get("followup_pending") is not None:
        # Was answering a follow-up
        q_text = state["followup_pending"]["q"]
        dept = state["followup_pending"]["dept"]
        cat = state["followup_pending"]["category"]
    elif idx > 0 and idx - 1 < len(questions):
        prev = questions[idx - 1]
        q_text = prev["q"]
        dept = prev["dept"]
        cat = prev["category"]
    else:
        q_text = ""
        dept = session.current_department or "General"
        cat = "general"

    result = await InterviewService.process_answer(
        session=session,
        question_text=q_text,
        department=dept,
        category=cat,
        answer_text=request.message,
        user_id=str(current_user.id),
    )

    # If complete, finish the interview
    if result.get("session_complete"):
        await InterviewService.complete_interview(request.session_id)

    # Attach progress
    progress = await InterviewService.get_progress(request.session_id)
    result["progress"] = progress

    return result


# ─────────────────────────────────────────────────────────────────────────────
# LEGACY ENDPOINTS (kept for backward compatibility)
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/next-question/{session_id}")
async def get_next_question(
    session_id: str,
    current_user: User = Depends(get_current_user),
):
    """Legacy endpoint — returns None to signal use of /chat instead."""
    return {"status": "use_chat", "question": None}


@router.post("/answer")
async def submit_answer(
    request: InterviewAnswerRequest,
    current_user: User = Depends(get_current_user),
):
    """Legacy endpoint for direct answer submission."""
    answer = await AnswerService.submit_answer(
        session_id=request.session_id,
        question_id=request.question_id,
        answer_text=request.answer,
        user_id=str(current_user.id),
    )
    progress_data = await ProgressService.calculate_progress(request.session_id)
    return {
        "message": "Answer submitted successfully",
        "answer_id": str(answer.id),
        "progress": progress_data,
    }


@router.get("/progress/{session_id}")
async def get_progress(
    session_id: str,
    current_user: User = Depends(get_current_user),
):
    progress_data = await InterviewService.get_progress(session_id)
    return progress_data


@router.post("/complete/{session_id}")
async def complete_interview(
    session_id: str,
    current_user: User = Depends(get_current_user),
):
    session = await InterviewService.complete_interview(session_id)
    return {
        "message": "Interview completed and profile generated",
        "session_id": str(session.id),
    }


# ─────────────────────────────────────────────────────────────────────────────
# RECOMMENDATIONS
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/recommendations/{session_id}")
async def get_recommendations(
    session_id: str,
    current_user: User = Depends(get_current_user),
):
    """Return grouped document recommendations generated from the interview."""
    recs = await RecommendationEngine.get_recommendations(session_id)

    # Group by department
    grouped: Dict[str, List] = {}
    for r in recs:
        if r.department not in grouped:
            grouped[r.department] = []
        grouped[r.department].append({
            "document_name": r.document_name,
            "priority": r.priority,
            "reason": r.reason,
        })

    departments = [
        {"department": dept, "documents": docs}
        for dept, docs in grouped.items()
    ]

    session = await InterviewSession.get(session_id)
    return {
        "session_id": session_id,
        "workspace_id": session.workspace_id if session else "",
        "recommendations": departments,
        "generated_at": datetime.utcnow().isoformat(),
    }


# ─────────────────────────────────────────────────────────────────────────────
# COMPANY PROFILE (enriched post-interview)
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/company-profile/{workspace_id}")
async def get_company_profile(
    workspace_id: str,
    current_user: User = Depends(get_current_user),
):
    profile = await CompanyProfile.find_one({"workspace_id": workspace_id})
    if not profile:
        raise HTTPException(status_code=404, detail="Company profile not found")
    return profile
