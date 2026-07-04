from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Optional
from app.core.dependencies import get_current_user
from app.models.user import User
from app.services.interview_service import InterviewService
from app.services.chat_service import ChatService
from app.services.knowledge_service import KnowledgeService
from app.services.company_profile_service import CompanyProfileService
from app.models.company_profile import CompanyProfile

router = APIRouter()


# --- REAL-TIME ANALYSIS (workspace creation preview) ---

class AnalyzeTextRequest(BaseModel):
    name: str
    description: str

@router.post("/analyze-text")
async def analyze_text(req: AnalyzeTextRequest):
    """
    Lightweight NLP extraction from workspace name + description.
    Called in real-time as the user types in the Create Workspace modal.
    No auth required — it is a preview-only, stateless call.
    """
    result = await CompanyProfileService.analyze_text(req.name, req.description)
    return result

# --- INTERVIEW ENDPOINTS ---

class StartInterviewRequest(BaseModel):
    organization_id: str
    department: str

class SubmitAnswerRequest(BaseModel):
    session_id: str
    answer: str

@router.post("/interview/start")
async def start_interview(
    req: StartInterviewRequest,
    current_user: User = Depends(get_current_user)
):
    session = await InterviewService.start_interview(req.organization_id, req.department)
    return {"session_id": str(session.id), "history": session.history, "status": session.status}

@router.post("/interview/answer")
async def submit_answer(
    req: SubmitAnswerRequest,
    current_user: User = Depends(get_current_user)
):
    next_question = await InterviewService.submit_answer(req.session_id, req.answer)
    return {"next_question": next_question}

# --- CHAT ENDPOINTS ---

class ChatRequest(BaseModel):
    session_id: str
    workspace_id: str
    message: str

@router.post("/chat")
async def chat_with_brain(
    req: ChatRequest,
    current_user: User = Depends(get_current_user)
):
    response = await ChatService.process_chat_message(
        session_id=req.session_id,
        user_id=str(current_user.id),
        workspace_id=req.workspace_id,
        message=req.message
    )
    return {"reply": response}

# --- PROFILE ENDPOINTS ---

@router.post("/profile/synthesize")
async def synthesize_profile(
    organization_id: str,
    current_user: User = Depends(get_current_user)
):
    """Manually triggers the synthesis of the company profile."""
    profile = await KnowledgeService.synthesize_company_profile(organization_id)
    return profile

@router.get("/profile/{org_id}", response_model=CompanyProfile)
async def get_profile(
    org_id: str,
    current_user: User = Depends(get_current_user)
):
    profile = await CompanyProfile.find_one(CompanyProfile.organization_id == org_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Company profile not found or not synthesized yet.")
    return profile
