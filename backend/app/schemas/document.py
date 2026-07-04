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
    version: str
    mime_type: str | None = None
    chunk_count: int = 0
    embedding_count: int = 0
    extracted_metadata: dict = {}
    knowledge_score: float = 0.0
    learning_progress: float = 0.0
    error_message: str | None = None
    department: str | None = None
    created_at: datetime
    updated_at: datetime


class DocumentUpdate(BaseModel):
    name: str | None = None
    status: str | None = None
    version: str | None = None