"""Application constants grouped by responsibility."""


class ValidationLimits:
    """Registration and login input limits and password policy."""

    MIN_NAME_LENGTH = 1
    MAX_NAME_LENGTH = 100
    MIN_PASSWORD_LENGTH = 8
    MAX_PASSWORD_LENGTH = 128
    MIN_LOGIN_PASSWORD_LENGTH = 1
    PASSWORD_COMPLEXITY_PATTERN = r"(?=.*[A-Z])(?=.*[a-z])(?=.*[0-9])(?=.*[!-\/:-@\[-`{-~])"
    PASSWORD_REQUIREMENTS = (
        "Password must include an uppercase letter, a lowercase letter, a number, and a special character."
    )


class AuthValues:
    """Token types and authentication cookie settings."""

    ACCESS_TOKEN = "access"
    REFRESH_TOKEN = "refresh"
    ACCESS_COOKIE = "access_token"
    REFRESH_COOKIE = "refresh_token"
    COOKIE_SAMESITE = "strict"
    COOKIE_PATH = "/"


class LogSettings:
    """Log file location and retention policy."""

    LOG_RETENTION_DAYS = 7
    LOG_CLEANUP_INTERVAL_SECONDS = 3600
    LOG_DIRECTORY_NAME = "logs"
    LOG_FILE_NAME = "application.log"


class ApiPaths:
    """Constants for api paths."""

    API_PREFIX = "/api"
    AUTH_PREFIX = "/auth"
    REGISTER_PATH = "/register"
    LOGIN_PATH = "/login"
    REFRESH_PATH = "/refresh"
    LOGOUT_PATH = "/logout"
    PROFILE_PATH = "/me"
    USERS_PATH = "/users"


class ApiMessages:
    """Constants for api messages."""

    INVALID_ORIGIN_MESSAGE = "Invalid request origin"
    INVALID_AUTH_HEADER_MESSAGE = "Invalid authorization header"
    AUTH_REQUIRED_MESSAGE = "Authentication required"
    INVALID_SESSION_MESSAGE = "Invalid or expired session"
    INVALID_CREDENTIALS_MESSAGE = "Invalid email or password"
    FORBIDDEN_MESSAGE = "Insufficient permissions"
    DUPLICATE_MESSAGE = "A record with this value already exists"
    VALIDATION_MESSAGE = "Please check the submitted information"
    UNEXPECTED_ERROR_MESSAGE = "An unexpected error occurred"
    REGISTER_SUCCESS_MESSAGE = "Account created"
    LOGIN_SUCCESS_MESSAGE = "Signed in"
    REFRESH_SUCCESS_MESSAGE = "Session refreshed"
    LOGOUT_SUCCESS_MESSAGE = "Signed out"
    PROFILE_SUCCESS_MESSAGE = "Profile retrieved"
    USERS_SUCCESS_MESSAGE = "Users retrieved"
