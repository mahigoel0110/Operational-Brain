from pydantic import (
    BaseModel,
    EmailStr,
    Field,
    ConfigDict,
    field_validator
)

import re


class UserCreate(BaseModel):

    name: str = Field(
        min_length=3,
        max_length=50
    )

    email: EmailStr

    password: str = Field(
        min_length=8,
        max_length=100
    )

    role: str | None = Field(default="Operations Director")
    department: str | None = Field(default=None)

    @field_validator("name")
    @classmethod
    def validate_name(cls, value):

        if not value.replace(" ", "").isalpha():
            raise ValueError(
                "Name should contain only alphabets"
            )

        return value.title()

    @field_validator("password")
    @classmethod
    def validate_password(cls, value):

        if not re.search(r"[A-Z]", value):
            raise ValueError(
                "Password must contain one uppercase letter."
            )

        if not re.search(r"[a-z]", value):
            raise ValueError(
                "Password must contain one lowercase letter."
            )

        if not re.search(r"[0-9]", value):
            raise ValueError(
                "Password must contain one digit."
            )

        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", value):
            raise ValueError(
                "Password must contain one special character."
            )

        return value


class UserLogin(BaseModel):

    email: EmailStr

    password: str


class UserResponse(BaseModel):

    id: str
    name: str
    email: EmailStr
    role: str | None = "Operations Director"
    department: str | None = None

    model_config = ConfigDict(
        from_attributes=True
    )

class UpdateProfile(BaseModel):

    name: str = Field(
        min_length=3,
        max_length=50
    )


class ChangePassword(BaseModel):

    old_password: str

    new_password: str = Field(
        min_length=8
    )

class ForgotPassword(BaseModel):
    email: EmailStr

class ResetPassword(BaseModel):
    token: str
    new_password: str = Field(
        min_length=8,
        max_length=100
    )

    @field_validator("new_password")
    @classmethod
    def validate_password(cls, value):

        if not re.search(r"[A-Z]", value):
            raise ValueError(
                "Password must contain one uppercase letter."
            )

        if not re.search(r"[a-z]", value):
            raise ValueError(
                "Password must contain one lowercase letter."
            )

        if not re.search(r"[0-9]", value):
            raise ValueError(
                "Password must contain one digit."
            )

        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", value):
            raise ValueError(
                "Password must contain one special character."
            )

        return value