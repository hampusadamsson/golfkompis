"""Pydantic schemas for fastapi-users endpoints."""

import uuid

from fastapi_users import schemas


class UserRead(schemas.BaseUser[uuid.UUID]):
    username: str | None = None
    full_name: str | None = None
    mingolf_username: str | None = None
    mingolf_password: str | None = None


class UserCreate(schemas.BaseUserCreate):
    username: str | None = None
    full_name: str | None = None


class UserUpdate(schemas.BaseUserUpdate):
    username: str | None = None
    full_name: str | None = None
    mingolf_username: str | None = None
    mingolf_password: str | None = None
