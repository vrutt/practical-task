import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase


def get_current_utc_time():
    """Return the current UTC time as a naive timestamp."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


class Base(DeclarativeBase):
    pass


class CustomBaseModel(Base):
    """
    Base class for all database models.

    This class defines the ``id`` column as a UUID, and the ``created_at`` and ``updated_at``
    columns as timestamps. The ``created_at`` column is set when the row is inserted, and the
    ``updated_at`` column is set every time the row is updated.
    """

    __abstract__ = True

    id = Column(
        UUID(as_uuid=False),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        unique=True,
        index=True,
        nullable=False,
    )
    created_at = Column(
        DateTime,
        default=get_current_utc_time,
        server_default=func.now(),
        nullable=False,
    )
    updated_at = Column(
        DateTime,
        default=get_current_utc_time,
        onupdate=get_current_utc_time,
        server_default=func.now(),
        nullable=False,
    )
