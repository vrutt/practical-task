import asyncio
import logging
from contextlib import asynccontextmanager, suppress

from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_swagger_ui_html

from app.config.database import create_database_engine, create_session_factory
from app.config.logging import close_logging, configure_logging
from app.config.settings import settings
from app.middleware.errors import register_exception_handlers
from app.modules import user_router
from app.security.cleanup import cleanup_auth_records
from app.security.rate_limit import limiter
from app.utils.base_schema import ErrorResponse
from app.utils.constant import ApiPaths, AuthenticationPolicy, LogSettings


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Create the database engine for the application lifetime."""
    engine = create_database_engine()
    handler = configure_logging()

    async def purge_logs():
        while True:
            await asyncio.sleep(LogSettings.LOG_CLEANUP_INTERVAL_SECONDS)
            try:
                handler.purge_expired()
            except OSError:
                logging.getLogger(__name__).exception("Log retention cleanup failed")

    app.state.db_engine = engine
    app.state.db_session_factory = create_session_factory(engine)

    async def purge_auth_records():
        while True:
            try:
                await cleanup_auth_records(app.state.db_session_factory)
            except Exception:
                logging.getLogger(__name__).exception("Authentication record cleanup failed")
            await asyncio.sleep(AuthenticationPolicy.CLEANUP_INTERVAL_SECONDS)

    retention_task = asyncio.create_task(purge_logs())
    auth_cleanup_task = asyncio.create_task(purge_auth_records())
    try:
        yield
    finally:
        retention_task.cancel()
        auth_cleanup_task.cancel()
        with suppress(asyncio.CancelledError):
            await retention_task
        with suppress(asyncio.CancelledError):
            await auth_cleanup_task
        await engine.dispose()
        close_logging(handler)


app = FastAPI(
    title="Authentication API", debug=settings.DEBUG, lifespan=lifespan, docs_url=None, servers=[{"url": "."}]
)
app.state.limiter = limiter
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=settings.allowed_methods,
    allow_headers=settings.allowed_headers,
)
register_exception_handlers(app)
app.include_router(
    user_router,
    prefix=ApiPaths.AUTH_PREFIX,
    tags=["Authentication"],
    responses={
        status.HTTP_401_UNAUTHORIZED: {"model": ErrorResponse, "description": "Authentication failed"},
        status.HTTP_403_FORBIDDEN: {"model": ErrorResponse, "description": "Request origin is not allowed"},
        status.HTTP_409_CONFLICT: {"model": ErrorResponse, "description": "Account already exists"},
        status.HTTP_429_TOO_MANY_REQUESTS: {"model": ErrorResponse, "description": "Too many login attempts"},
        status.HTTP_422_UNPROCESSABLE_CONTENT: {"model": ErrorResponse, "description": "Invalid input"},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"model": ErrorResponse, "description": "Unexpected server error"},
    },
)


@app.get("/docs", include_in_schema=False)
async def documentation():
    """Resolve the schema beside this page for direct and proxied access."""
    return get_swagger_ui_html(openapi_url="openapi.json", title="Authentication API documentation")
