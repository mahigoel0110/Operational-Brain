from datetime import datetime, UTC
from beanie import Document
from pydantic import Field


class DocumentModel(Document):
    name: str = Field(..., min_length=1, max_length=255)
    workspace_id: str
    uploaded_by: str
    storage_path: str
    file_size: int
    status: str = Field(default="uploaded")  # e.g., uploaded, processing, embedding, ready, failed
    version: str = Field(default="1.0")
    mime_type: str | None = None
    chunk_count: int = Field(default=0)
    embedding_count: int = Field(default=0)
    extracted_metadata: dict = Field(default_factory=dict)
    knowledge_score: float = Field(default=0.0)
    learning_progress: float = Field(default=0.0)
    error_message: str | None = None
    department: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    class Settings:
        name = "documents"

    class Config:
        json_schema_extra = {
            "example": {
                "name": "manual.pdf",
                "workspace_id": "workspace_id_hash",
                "uploaded_by": "user_id_hash",
                "storage_path": "uploads/workspace_id_hash/manual.pdf",
                "file_size": 1048576,
                "status": "active",
                "version": "1.0",
                "mime_type": "application/pdf"
            }
        }
