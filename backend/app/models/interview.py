from datetime import datetime, UTC
from beanie import Document
from pydantic import Field
from typing import Optional, List, Dict

class InterviewSession(Document):
    workspace_id: str
    created_by: str
    status: str = Field(default="in_progress")  # in_progress, completed
    started_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    completed_at: Optional[datetime] = None
    current_department: Optional[str] = None
    progress: dict = Field(default_factory=dict)
    completion_percentage: int = Field(default=0)
    # Detected industry from workspace profile
    detected_industry: Optional[str] = None
    # Ordered list of departments to cover
    department_queue: List[str] = Field(default_factory=list)
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    class Settings:
        name = "interview_sessions"


class InterviewQuestion(Document):
    department: str
    question: str
    order: int
    required: bool = Field(default=True)
    category: Optional[str] = None
    industry: Optional[str] = None        # None = universal
    follow_up_for: Optional[str] = None   # keyword that triggers this as follow-up

    class Settings:
        name = "interview_questions"


class InterviewAnswer(Document):
    session_id: str
    question_id: str
    question_text: str = Field(default="")   # store question text for context
    answer: str
    answered_by: str
    department: str = Field(default="General")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))

    class Settings:
        name = "interview_answers"


class InterviewProgress(Document):
    """Tracks detailed progress metrics per session."""
    session_id: str
    workspace_id: str
    knowledge_score: int = Field(default=0)           # 0–100 overall knowledge captured
    department_confidence: Dict[str, int] = Field(default_factory=dict)  # dept → 0–100
    missing_info: List[str] = Field(default_factory=list)                # topics not yet covered
    questions_asked: int = Field(default=0)
    questions_answered: int = Field(default=0)
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    class Settings:
        name = "interview_progress"


class InterviewRecommendation(Document):
    """Document recommendations generated after interview completion."""
    session_id: str
    workspace_id: str
    department: str
    document_name: str
    priority: str = Field(default="medium")  # high, medium, low
    reason: str = Field(default="")
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    class Settings:
        name = "interview_recommendations"
