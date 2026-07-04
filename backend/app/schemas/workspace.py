from datetime import datetime
from pydantic import BaseModel, Field


class WorkspaceCreate(BaseModel):

    organization_id: str

    name: str = Field(
        min_length=2,
        max_length=100
    )

    description: str = Field(
        default="",
        max_length=1000
    )

    workspace_type: str = "General"


class WorkspaceUpdate(BaseModel):

    name: str | None = None
    description: str | None = None
    workspace_type: str | None = None


class WorkspaceResponse(BaseModel):

    id: str

    organization_id: str

    name: str

    description: str

    workspace_type: str

    created_by: str

    created_at: datetime

    updated_at: datetime