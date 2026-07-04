from datetime import datetime, UTC
from beanie import Document
from pydantic import Field
from typing import List, Dict

class ChatSession(Document):
    user_id: str
    workspace_id: str
    
    # Standard OpenAI format: [{"role": "user", "content": "..."}]
    messages: List[Dict[str, str]] = Field(default_factory=list)
    
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    class Settings:
        name = "chat_sessions"
