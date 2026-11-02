from typing import Generic, TypeVar

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.utils.base_model import Base

ModelT = TypeVar("ModelT", bound=Base)


class BaseRepository(Generic[ModelT]):
    """Shared persistence operations; the request owns transaction commit/rollback."""

    def __init__(self, db: AsyncSession, model: type[ModelT]):
        self.db = db
        self.model = model

    async def add(self, entity: ModelT) -> ModelT:
        """Add and flush an entity within the current transaction."""
        self.db.add(entity)
        await self.db.flush()
        return entity

    async def by_id(self, entity_id: str) -> ModelT | None:
        """Find an entity by its primary key."""
        return await self.db.get(self.model, entity_id)

    async def list_all(self) -> list[ModelT]:
        """Return entities in a stable creation order."""
        result = await self.db.scalars(select(self.model).order_by(self.model.created_at, self.model.id))
        return list(result)

    async def update(self, entity: ModelT, **changes) -> ModelT:
        """Apply and flush changes to an entity."""
        for field, value in changes.items():
            if not hasattr(self.model, field):
                raise ValueError(f"Unknown {self.model.__name__} field: {field}")
            setattr(entity, field, value)
        await self.db.flush()
        return entity

    async def delete(self, entity: ModelT) -> None:
        """Delete and flush an entity."""
        await self.db.delete(entity)
        await self.db.flush()
