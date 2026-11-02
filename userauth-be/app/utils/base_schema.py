from typing import Generic, Literal, TypeVar

from pydantic import BaseModel, ConfigDict

DataT = TypeVar("DataT")
ErrorT = TypeVar("ErrorT")


class RequestSchema(BaseModel):
    """Shared request policy: reject unexpected input fields."""

    model_config = ConfigDict(extra="forbid")


class ResponseEnvelope(BaseModel, Generic[DataT, ErrorT]):
    success: bool
    message: str
    data: DataT | None = None
    errors: ErrorT | None = None


class SuccessResponse(ResponseEnvelope[DataT, None], Generic[DataT]):
    success: Literal[True] = True


class ValidationIssue(BaseModel):
    field: str
    message: str


class ErrorResponse(ResponseEnvelope[None, list[ValidationIssue]]):
    success: Literal[False] = False
