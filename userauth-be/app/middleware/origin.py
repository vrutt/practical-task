from fastapi import HTTPException, Request, status

from app.config.settings import settings
from app.utils.constant import ApiMessages


class OriginGuard:
    def __call__(self, request: Request) -> None:
        """Reject state-changing requests from origins outside the allowlist."""
        if request.headers.get("origin") not in settings.allowed_origins:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=ApiMessages.INVALID_ORIGIN_MESSAGE)


origin_guard = OriginGuard()
