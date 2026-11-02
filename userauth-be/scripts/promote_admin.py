"""Promote an existing account from a trusted terminal: python -m scripts.promote_admin EMAIL."""

import argparse
import asyncio

from app.config.database import create_database_engine, create_session_factory
from app.modules.user.repository import UserRepository
from app.modules.user.schemas import RoleType


async def promote(email: str) -> None:
    engine = create_database_engine()
    try:
        factory = create_session_factory(engine)
        async with factory() as db:
            user = await UserRepository(db).by_email(email.strip().lower())
            if user is None:
                raise SystemExit("No user found with that email.")
            await UserRepository(db).update(user, role=RoleType.Admin)
            await db.commit()
            print("Account promoted to Admin.")
    finally:
        await engine.dispose()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Promote an existing account to Admin")
    parser.add_argument("email")
    asyncio.run(promote(parser.parse_args().email))
