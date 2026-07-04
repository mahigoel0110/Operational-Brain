from datetime import datetime, UTC

from beanie import Document
from pydantic import Field


class Organization(Document):
    name: str = Field(
        ...,
        min_length=2,
        max_length=100
    )

    industry: str = Field(
        ...,
        min_length=2,
        max_length=100
    )

    description: str = Field(
        default="",
        max_length=1000
    )

    owner_id: str
    members: list[str] = Field(default_factory=list)

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC)
    )

    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC)
    )

    class Settings:
        name = "organizations"