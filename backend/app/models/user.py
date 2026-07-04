from beanie import Document
from pydantic import EmailStr, Field
from datetime import datetime, UTC


class User(Document):
    name: str
    email: EmailStr
    hashed_password: str

    is_active: bool = True
    is_verified: bool = False

    role: str = Field(default="Operations Director")
    department: str | None = Field(default=None)

    reset_token: str | None = None
    reset_token_expiry: datetime | None = None

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC)
    )

    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC)
    )

    class Settings:
        name = "users"

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Mahi",
                "email": "mahi@gmail.com"
            }
        }