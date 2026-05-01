"""Tests for PATCH /users/me/mingolf — verify-before-persist flow."""

from __future__ import annotations

import pathlib
from unittest.mock import patch

import pytest
from asgi_lifespan import LifespanManager
from httpx import ASGITransport, AsyncClient

from golfkompis.app import app
from golfkompis.mingolf import InvalidCredentials


@pytest.fixture(autouse=True)
def isolated_db(tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

    import golfkompis.users.db as db_module

    url = f"sqlite+aiosqlite:///{tmp_path}/test.db"
    engine = create_async_engine(url, connect_args={"check_same_thread": False})
    session_maker = async_sessionmaker(engine, expire_on_commit=False)
    monkeypatch.setattr(db_module, "_engine", engine)  # pyright: ignore[reportUnknownMemberType]
    monkeypatch.setattr(db_module, "_async_session_maker", session_maker)  # pyright: ignore[reportUnknownMemberType]


async def _register_and_login(
    client: AsyncClient, email: str = "user@test.com", password: str = "password123"
) -> None:
    r = await client.post("/auth/register", json={"email": email, "password": password})
    assert r.status_code == 201
    r = await client.post(
        "/auth/login",
        data={"username": email, "password": password},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert r.status_code == 204


async def test_patch_mingolf_clear_both_null() -> None:
    """Sending both null clears creds without calling MinGolf."""
    with patch("golfkompis.mingolf.MinGolf.login") as mock_login:
        async with LifespanManager(app):
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                await _register_and_login(client)
                r = await client.patch(
                    "/users/me/mingolf",
                    json={"mingolf_username": None, "mingolf_password": None},
                )
    assert r.status_code == 200
    mock_login.assert_not_called()
    data = r.json()
    assert data["mingolf_username"] is None
    assert data["mingolf_password"] is None


async def test_patch_mingolf_invalid_creds_rejected() -> None:
    """MinGolf login failing → 422 with detail=mingolf_invalid."""
    with patch(
        "golfkompis.mingolf.MinGolf.login", side_effect=InvalidCredentials("bad")
    ):
        async with LifespanManager(app):
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                await _register_and_login(client)
                r = await client.patch(
                    "/users/me/mingolf",
                    json={
                        "mingolf_username": "123456-789",
                        "mingolf_password": "wrongpass",
                    },
                )
    assert r.status_code == 422
    assert r.json()["detail"] == "mingolf_invalid"


async def test_patch_mingolf_partial_rejected() -> None:
    """Only one field set → 422 with detail=mingolf_incomplete."""
    async with (
        LifespanManager(app),
        AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client,
    ):
        await _register_and_login(client)
        r = await client.patch(
            "/users/me/mingolf",
            json={"mingolf_username": "123456-789", "mingolf_password": None},
        )
    assert r.status_code == 422
    assert r.json()["detail"] == "mingolf_incomplete"


async def test_patch_mingolf_valid_creds_saved() -> None:
    """Valid MinGolf creds are saved and returned in response."""
    with patch("golfkompis.mingolf.MinGolf.login"):  # no exception = success
        async with LifespanManager(app):
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                await _register_and_login(client)
                r = await client.patch(
                    "/users/me/mingolf",
                    json={
                        "mingolf_username": "123456-789",
                        "mingolf_password": "mypass",
                    },
                )
    assert r.status_code == 200
    data = r.json()
    assert data["mingolf_username"] == "123456-789"
    assert data["mingolf_password"] == "mypass"


async def test_patch_mingolf_unauthenticated() -> None:
    """Anonymous request → 401."""
    async with (
        LifespanManager(app),
        AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client,
    ):
        r = await client.patch(
            "/users/me/mingolf",
            json={"mingolf_username": None, "mingolf_password": None},
        )
    assert r.status_code == 401
