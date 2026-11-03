import re
from datetime import datetime, timezone
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.utils.base_schema import RequestSchema, SuccessResponse
from app.utils.constant import ValidationLimits


class RoleType(Enum):
    Admin = "Admin"
    User = "User"


class InvalidCredentialsError(Exception):
    """The supplied login credentials are invalid."""


class InvalidSessionError(Exception):
    """The supplied session is missing, expired or revoked."""


class Registration(RequestSchema):
    name: str = Field(min_length=ValidationLimits.MIN_NAME_LENGTH, max_length=ValidationLimits.MAX_NAME_LENGTH)
    email: EmailStr
    password: str = Field(
        min_length=ValidationLimits.MIN_PASSWORD_LENGTH,
        max_length=ValidationLimits.MAX_PASSWORD_LENGTH,
        description=ValidationLimits.PASSWORD_REQUIREMENTS,
    )

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str) -> str:
        """Enforce the password complexity policy for new registrations."""
        if not re.search(ValidationLimits.PASSWORD_COMPLEXITY_PATTERN, value):
            raise ValueError(ValidationLimits.PASSWORD_REQUIREMENTS)
        return value

    @field_validator("name")
    @classmethod
    def clean_name(cls, value: str) -> str:
        """Remove surrounding whitespace and reject blank names."""
        value = value.strip()
        if not value:
            raise ValueError("Name cannot be blank")
        return value


class Login(RequestSchema):
    email: EmailStr
    password: str = Field(
        min_length=ValidationLimits.MIN_LOGIN_PASSWORD_LENGTH, max_length=ValidationLimits.MAX_PASSWORD_LENGTH
    )


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    name: str
    email: EmailStr
    role: RoleType
    created_at: datetime

    @field_validator("created_at")
    @classmethod
    def normalize_created_at(cls, value: datetime) -> datetime:
        """Expose stored UTC timestamps with an explicit timezone."""
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)


class UserSuccessResponse(SuccessResponse[UserResponse]):
    pass


class UserListSuccessResponse(SuccessResponse[list[UserResponse]]):
    pass


class EmptySuccessResponse(SuccessResponse[None]):
    pass
