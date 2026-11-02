"""Centralized error responses for the API."""

import logging
import sqlite3

from asyncpg.exceptions import UniqueViolationError
from fastapi import FastAPI, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError
from starlette.exceptions import HTTPException

from app.modules.user.schemas import InvalidCredentialsError, InvalidSessionError
from app.utils.constant import ApiMessages

logger = logging.getLogger(__name__)


def error_response(status_code: int, message: str, errors=None, headers=None):
    """Build the standard API error response."""
    return JSONResponse(
        status_code=status_code,
        headers=headers,
        content=jsonable_encoder(
            {
                "success": False,
                "message": message,
                "data": None,
                "errors": errors,
            }
        ),
    )


def register_exception_handlers(app: FastAPI):
    """Register consistent handlers for expected and unexpected errors."""

    @app.exception_handler(IntegrityError)
    async def handle_integrity_error(request: Request, exc: IntegrityError):
        """Translate unique violations without exposing database values or SQL."""
        original = exc.orig
        cause = getattr(original, "__cause__", None)
        sqlstate = getattr(original, "sqlstate", None) or getattr(cause, "sqlstate", None)
        sqlite_code = getattr(original, "sqlite_errorcode", None)
        if sqlstate == UniqueViolationError.sqlstate or sqlite_code in (
            sqlite3.SQLITE_CONSTRAINT_PRIMARYKEY,
            sqlite3.SQLITE_CONSTRAINT_UNIQUE,
        ):
            return error_response(status.HTTP_409_CONFLICT, ApiMessages.DUPLICATE_MESSAGE)
        logger.error("Database integrity error; request could not be completed")
        return error_response(status.HTTP_500_INTERNAL_SERVER_ERROR, ApiMessages.UNEXPECTED_ERROR_MESSAGE)

    @app.exception_handler(InvalidCredentialsError)
    async def handle_invalid_credentials(request: Request, exc: InvalidCredentialsError):
        """Hide whether a login email exists."""
        return error_response(status.HTTP_401_UNAUTHORIZED, ApiMessages.INVALID_CREDENTIALS_MESSAGE)

    @app.exception_handler(InvalidSessionError)
    async def handle_invalid_session(request: Request, exc: InvalidSessionError):
        """Return a consistent response for invalid refresh sessions."""
        return error_response(status.HTTP_401_UNAUTHORIZED, ApiMessages.INVALID_SESSION_MESSAGE)

    @app.exception_handler(HTTPException)
    async def handle_http_error(request: Request, exc: HTTPException):
        """Convert HTTP exceptions to the common response format."""
        return error_response(exc.status_code, str(exc.detail), headers=exc.headers)

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(request: Request, exc: RequestValidationError):
        # Do not echo submitted input, which may include passwords.
        """Return field errors without echoing submitted values."""
        errors = [
            {"field": ".".join(str(part) for part in e["loc"] if part != "body"), "message": e["msg"]}
            for e in exc.errors()
        ]
        return error_response(status.HTTP_422_UNPROCESSABLE_CONTENT, ApiMessages.VALIDATION_MESSAGE, errors)

    @app.exception_handler(Exception)
    async def handle_unexpected_error(request: Request, exc: Exception):
        """Log unexpected failures and return a generic error."""
        logger.exception("Unhandled API error", exc_info=exc)
        return error_response(status.HTTP_500_INTERNAL_SERVER_ERROR, ApiMessages.UNEXPECTED_ERROR_MESSAGE)
