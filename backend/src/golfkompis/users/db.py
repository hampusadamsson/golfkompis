"""Async SQLAlchemy setup for the user-management DB."""

from collections.abc import AsyncGenerator

from fastapi import Depends
from fastapi_users.db import SQLAlchemyUserDatabase
from fastapi_users_db_sqlalchemy.access_token import SQLAlchemyAccessTokenDatabase
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from golfkompis.config import settings

_engine = create_async_engine(settings.auth_database_url)
_async_session_maker = async_sessionmaker(_engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def create_db_and_tables() -> None:
    """Create all tables defined on Base. Called once at app startup."""
    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_async_session() -> AsyncGenerator[AsyncSession]:
    async with _async_session_maker() as session:
        yield session


async def get_user_db(  # pyright: ignore[reportUnknownParameterType]
    session: AsyncSession = Depends(get_async_session),
) -> AsyncGenerator[SQLAlchemyUserDatabase]:  # type: ignore[type-arg]
    from golfkompis.users.models import User

    yield SQLAlchemyUserDatabase(session, User)


async def get_access_token_db(  # pyright: ignore[reportUnknownParameterType]
    session: AsyncSession = Depends(get_async_session),
) -> AsyncGenerator[SQLAlchemyAccessTokenDatabase]:  # type: ignore[type-arg]
    from golfkompis.users.models import AccessToken

    yield SQLAlchemyAccessTokenDatabase(session, AccessToken)
