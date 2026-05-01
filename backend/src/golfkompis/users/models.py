"""SQLAlchemy ORM models for the user-management DB."""

from fastapi_users.db import SQLAlchemyBaseUserTableUUID
from fastapi_users_db_sqlalchemy.access_token import SQLAlchemyBaseAccessTokenTableUUID
from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from golfkompis.users.db import Base


class User(SQLAlchemyBaseUserTableUUID, Base):
    username: Mapped[str | None] = mapped_column(
        String(length=64), unique=True, index=True, nullable=True, default=None
    )
    full_name: Mapped[str | None] = mapped_column(
        String(length=128), nullable=True, default=None
    )
    age: Mapped[int | None] = mapped_column(Integer, nullable=True, default=None)


class AccessToken(SQLAlchemyBaseAccessTokenTableUUID, Base):
    pass
