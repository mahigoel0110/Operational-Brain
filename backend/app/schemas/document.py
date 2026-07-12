from pydantic import BaseModel
from datetime import datetime


class DocumentUploadResponse(BaseModel):
    upload_id: str
    filename: str
    file_size: int
    message: str


class DocumentResponse(BaseModel):
    id: str
    name: str
    workspace_id: str
    uploaded_by: str
    storage_path: str
    file_size: int
    status: str
    processing_progress: int
    current_step: str
    processing_started_at: datetime | None = None
    processing_completed_at: datetime | None = None
    chunk_count: int = 0
    embedding_count: int = 0
    knowledge_score: float = 0.0
    department: str | None = None
    error_message: str | None = None
    metadata: dict = {}
    created_at: datetime
    updated_at: datetime


class DocumentUpdate(BaseModel):
    name: str | None = None
    status: str | None = None
    version: str | None = None