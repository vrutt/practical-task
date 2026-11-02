from fastapi import Response

from app.config.settings import settings
from app.utils.constant import AuthValues


class CookieManager:
    @staticmethod
    def set_tokens(response: Response, tokens: tuple[str, str]) -> None:
        """Set HTTP-only access and refresh cookies."""
        for name, value, lifetime in (
            (AuthValues.ACCESS_COOKIE, tokens[0], int(settings.access_lifetime.total_seconds())),
            (AuthValues.REFRESH_COOKIE, tokens[1], int(settings.refresh_lifetime.total_seconds())),
        ):
            response.set_cookie(
                name,
                value,
                max_age=lifetime,
                httponly=True,
                secure=settings.COOKIE_SECURE,
                samesite=AuthValues.COOKIE_SAMESITE,
                path=AuthValues.COOKIE_PATH,
            )

    @staticmethod
    def clear(response: Response) -> None:
        """Clear authentication cookies."""
        for name in (AuthValues.ACCESS_COOKIE, AuthValues.REFRESH_COOKIE):
            response.delete_cookie(
                name,
                path=AuthValues.COOKIE_PATH,
                secure=settings.COOKIE_SECURE,
                httponly=True,
                samesite=AuthValues.COOKIE_SAMESITE,
            )
