from pydantic import BaseModel
from typing import Optional, Dict, List, Any

class InterviewStartRequest(BaseModel):
    workspace_id: str

class InterviewAnswerRequest(BaseModel):
    session_id: str
    question_id: str
    answer: str

# ── Chat endpoint ──────────────────────────────────────────────────────────
class InterviewChatRequest(BaseModel):
    session_id: str
    message: str                     # The user's typed answer / message

class AIMessage(BaseModel):
    role: str                        # "ai" | "user"
    content: str
    department: Optional[str] = None
    category: Optional[str] = None
    question_id: Optional[str] = None

class InterviewChatResponse(BaseModel):
    ai_message: str                  # The AI's next question or comment
    question_id: Optional[str]       # ID of next question (None if complete)
    department: Optional[str]
    category: Optional[str]
    is_followup: bool = False
    session_complete: bool = False
    progress: Optional[Dict[str, Any]] = None

# ── Recommendations ────────────────────────────────────────────────────────
class RecommendedDocument(BaseModel):
    document_name: str
    priority: str                    # high | medium | low
    reason: str

class DepartmentRecommendation(BaseModel):
    department: str
    documents: List[RecommendedDocument]

class RecommendationResponse(BaseModel):
    session_id: str
    workspace_id: str
    recommendations: List[DepartmentRecommendation]
    generated_at: str

# ── Progress ───────────────────────────────────────────────────────────────
class ProgressResponse(BaseModel):
    progress: Dict[str, int]
    completion_percentage: int
    current_department: Optional[str]
    knowledge_score: int
    department_confidence: Dict[str, int]
    missing_info: List[str]
    questions_asked: int
    questions_answered: int
