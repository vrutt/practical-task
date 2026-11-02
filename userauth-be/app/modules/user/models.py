from sqlalchemy import Boolean, Column, DateTime, Enum, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID

from app.modules.user.schemas import RoleType
from app.utils.base_model import CustomBaseModel
from app.utils.constant import ValidationLimits


class User(CustomBaseModel):
    __tablename__ = "user"

    name = Column(String(ValidationLimits.MAX_NAME_LENGTH), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password = Column(String(255), nullable=False)
    role = Column(Enum(RoleType), default=RoleType.User, nullable=False)
    email_verified = Column(Boolean, nullable=False, default=False)


class RefreshToken(CustomBaseModel):
    __tablename__ = "refresh_tokens"

    user_id = Column(UUID(as_uuid=False), ForeignKey("user.id", ondelete="CASCADE"), nullable=False, index=True)
    token_hash = Column(String(64), unique=True, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    revoked_at = Column(DateTime, nullable=True)
