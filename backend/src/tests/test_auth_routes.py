"""Integration tests for user auth routes (register / login / me / logout).

Uses an in-memory SQLite database via httpx.AsyncClient + asgi-lifespan.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator
from typing import Any

import httpx
import pytest
from asgi_lifespan import LifespanManager


@pytest.fixture(scope="module")
def anyio_backend() -> str:
    return "asyncio"


@pytest.fixture(scope="module")
async def test_app(tmp_path_factory: pytest.TempPathFactory) -> AsyncGenerator[Any]:  # pyright: ignore[reportUnknownParameterType]
    """Patch the users DB engine to an isolated tmp file and yield the ASGI app."""
    tmp = tmp_path_factory.mktemp("auth_db")
    tmp_url = f"sqlite+aiosqlite:///{tmp / 'test_users.db'}"

    from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

    import golfkompis.users.db as users_db

    test_engine = create_async_engine(tmp_url)
    users_db._engine = test_engine  # pyright: ignore[reportPrivateUsage]
    users_db._async_session_maker = async_sessionmaker(  # pyright: ignore[reportPrivateUsage]
        test_engine, expire_on_commit=False
    )

    from golfkompis.app import app

    async with LifespanManager(app):
        yield app


_USER = {
    "email": "golfer@example.com",
    "username": "golfer1",
    "password": "SecurePass123!",
    "full_name": "Golf Player",
}


def _fresh_client(app: Any) -> httpx.AsyncClient:
    return httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),  # type: ignore[arg-type]
        base_url="http://test",
    )


@pytest.mark.asyncio
async def test_register(test_app: Any) -> None:
    async with _fresh_client(test_app) as c:
        r = await c.post("/auth/register", json=_USER)
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["email"] == _USER["email"]
    assert body["username"] == _USER["username"]
    assert "hashed_password" not in body


@pytest.mark.asyncio
async def test_login(test_app: Any) -> None:
    async with _fresh_client(test_app) as c:
        r = await c.post(
            "/auth/login",
            data={"username": _USER["email"], "password": _USER["password"]},
        )
    # fastapi-users cookie transport returns 204 on successful login
    assert r.status_code == 204, r.text


@pytest.mark.asyncio
async def test_me_unauthenticated(test_app: Any) -> None:
    async with _fresh_client(test_app) as c:
        r = await c.get("/users/me")
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_me_authenticated(test_app: Any) -> None:
    async with _fresh_client(test_app) as c:
        login = await c.post(
            "/auth/login",
            data={"username": _USER["email"], "password": _USER["password"]},
        )
        assert login.status_code == 204

        r = await c.get("/users/me")
    assert r.status_code == 200
    assert r.json()["email"] == _USER["email"]


@pytest.mark.asyncio
async def test_patch_me(test_app: Any) -> None:
    async with _fresh_client(test_app) as c:
        await c.post(
            "/auth/login",
            data={"username": _USER["email"], "password": _USER["password"]},
        )
        r = await c.patch("/users/me", json={"full_name": "Updated Name"})
    assert r.status_code == 200
    assert r.json()["full_name"] == "Updated Name"


@pytest.mark.asyncio
async def test_logout(test_app: Any) -> None:
    async with _fresh_client(test_app) as c:
        await c.post(
            "/auth/login",
            data={"username": _USER["email"], "password": _USER["password"]},
        )
        logout = await c.post("/auth/logout")
        assert logout.status_code == 204

        r = await c.get("/users/me")
    assert r.status_code == 401
