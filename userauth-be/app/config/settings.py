from datetime import timedelta

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Required application configuration, loaded from the environment or .env."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Application mode and debug behavior.
    DEBUG: bool
    ENVIRONMENT: str

    # PostgreSQL connection and pool settings (timeouts are in seconds).
    ASYNC_DATABASE_URL: str
    DATABASE_POOL_SIZE: int
    DATABASE_MAX_OVERFLOW: int
    DATABASE_POOL_TIMEOUT: int
    DATABASE_POOL_RECYCLE: int
    # JWT signing keys, algorithm and lifetime (days,hours,minutes,seconds).
    JWT_SECRET_KEY: str
    JWT_REFRESH_TOKEN_SECRET: str
    JWT_ALGORITHM: str
    JWT_ACCESS_TOKEN_LIFETIME: str
    JWT_REFRESH_TOKEN_LIFETIME: str
    # Comma-separated allowed browser origins, methods and headers.
    CORS_ALLOWED_ORIGINS: str
    CORS_ALLOWED_METHODS: str
    CORS_ALLOWED_HEADERS: str
    # Enable secure cookies for HTTPS deployments.
    COOKIE_SECURE: bool

    @field_validator("CORS_ALLOWED_ORIGINS")
    @classmethod
    def validate_origins(cls, value: str) -> str:
        """Require explicit origins for credentialed requests and the origin guard."""
        origins = cls.split_csv(value)
        if not origins or "*" in origins:
            raise ValueError("CORS_ALLOWED_ORIGINS must contain explicit comma-separated origins, not *")
        return value

    @field_validator("JWT_ACCESS_TOKEN_LIFETIME", "JWT_REFRESH_TOKEN_LIFETIME")
    @classmethod
    def validate_lifetime(cls, value: str) -> str:
        """Reject malformed, negative, zero or overflowing token lifetimes at startup."""
        cls.parse_lifetime(value)
        return value

    @staticmethod
    def parse_lifetime(value: str) -> timedelta:
        """Convert days,hours,minutes,seconds into a positive duration."""
        parts = value.split(",")
        if len(parts) != 4 or any(not part.strip().isascii() or not part.strip().isdigit() for part in parts):
            raise ValueError("Token lifetime must contain four nonnegative integers: days,hours,minutes,seconds")
        try:
            days, hours, minutes, seconds = (int(part.strip()) for part in parts)
            duration = timedelta(days=days, hours=hours, minutes=minutes, seconds=seconds)
        except (ValueError, OverflowError) as exc:
            raise ValueError("Invalid token lifetime") from exc
        if duration <= timedelta(0):
            raise ValueError("Token lifetime must be greater than zero")
        return duration

    @staticmethod
    def split_csv(value: str) -> list[str]:
        """Parse a comma-separated setting, trimming whitespace and empty entries."""
        return [item.strip() for item in value.split(",") if item.strip()]

    @property
    def allowed_origins(self) -> list[str]:
        return self.split_csv(self.CORS_ALLOWED_ORIGINS)

    @property
    def allowed_methods(self) -> list[str]:
        return self.split_csv(self.CORS_ALLOWED_METHODS)

    @property
    def allowed_headers(self) -> list[str]:
        return self.split_csv(self.CORS_ALLOWED_HEADERS)

    @property
    def access_lifetime(self) -> timedelta:
        return self.parse_lifetime(self.JWT_ACCESS_TOKEN_LIFETIME)

    @property
    def refresh_lifetime(self) -> timedelta:
        return self.parse_lifetime(self.JWT_REFRESH_TOKEN_LIFETIME)


settings = Settings()
