"""Pydantic schemas for fastapi-users endpoints."""

import uuid

from fastapi_users import schemas
from pydantic import Field


class UserRead(schemas.BaseUser[uuid.UUID]):
    username: str | None = None
    full_name: str | None = None
    age: int | None = None


class UserCreate(schemas.BaseUserCreate):
    username: str | None = None
    full_name: str | None = None
    age: int | None = Field(default=None, ge=0, le=150)


class UserUpdate(schemas.BaseUserUpdate):
    username: str | None = None
    full_name: str | None = None
    age: int | None = Field(default=None, ge=0, le=150)
