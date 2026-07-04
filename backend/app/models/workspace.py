from datetime import datetime, UTC

from beanie import Document
from pydantic import Field


class Workspace(Document):
    organization_id: str

    name: str = Field(..., min_length=2, max_length=100)

    description: str = Field(default="")

    workspace_type: str = Field(default="General")

    created_by: str

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC)
    )

    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC)
    )

    class Settings:
        name = "workspaces"