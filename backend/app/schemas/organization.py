from pydantic import BaseModel, Field


class OrganizationCreate(BaseModel):
    name: str = Field(min_length=2, max_length=100)

    industry: str = Field(min_length=2, max_length=100)

    description: str = Field(
        default="",
        max_length=1000
    )


class OrganizationUpdate(BaseModel):
    name: str | None = None

    industry: str | None = None

    description: str | None = None


class OrganizationResponse(BaseModel):
    id: str

    name: str

    industry: str

    description: str