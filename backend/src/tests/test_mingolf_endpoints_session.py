"""Integration tests: MinGolf endpoints require session cookie + DB-stored creds."""

from __future__ import annotations

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from asgi_lifespan import LifespanManager
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

# ── helpers ──────────────────────────────────────────────────────────────────


async def _register_and_login(client: AsyncClient, email: str, password: str) -> None:
    """Register + login an app user, leaving session cookie on client."""
    r = await client.post("/auth/register", json={"email": email, "password": password})
    assert r.status_code == 201
    r = await client.post(
        "/auth/login",
        data={"username": email, "password": password},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert r.status_code == 204


# ── fixtures ──────────────────────────────────────────────────────────────────


@pytest.fixture(autouse=True)
def isolated_db() -> None:
    """Each test gets its own isolated SQLite DB."""
    import golfkompis.users.db as users_db

    tmp = Path(tempfile.mkdtemp())
    tmp_url = f"sqlite+aiosqlite:///{tmp / 'test_users.db'}"
    test_engine = create_async_engine(tmp_url)
    users_db._engine = test_engine  # pyright: ignore[reportPrivateUsage]
    users_db._async_session_maker = async_sessionmaker(  # pyright: ignore[reportPrivateUsage]
        test_engine, expire_on_commit=False
    )


# ── tests ─────────────────────────────────────────────────────────────────────


async def test_get_profile_returns_401_when_not_logged_in() -> None:
    """Anonymous request → 401 (fastapi-users rejects immediately)."""
    from golfkompis.app import app

    async with (
        LifespanManager(app),
        AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client,
    ):
        r = await client.get("/api/v1/profile")
    assert r.status_code == 401


async def test_get_profile_returns_412_when_no_mingolf_link() -> None:
    """Logged-in user with no MinGolf creds → 412 mingolf_not_linked."""
    from golfkompis.app import app

    async with (
        LifespanManager(app),
        AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client,
    ):
        await _register_and_login(client, "nolink@test.com", "password123")
        r = await client.get("/api/v1/profile")
    assert r.status_code == 412
    assert r.json()["detail"] == "mingolf_not_linked"


async def test_get_profile_does_not_return_412_when_creds_stored() -> None:
    """Logged-in user with MinGolf creds stored → NOT 412 (proceeds to MinGolf call).

    We override get_authenticated_client so no real MinGolf network call is made.
    The key assertion is that storing creds bypasses the 412 guard.
    """
    import json
    from pathlib import Path

    from golfkompis.app import app, get_authenticated_client
    from golfkompis.domain import Profile
    from golfkompis.mingolf import MinGolf

    fixtures_dir = Path(__file__).parent.parent / "golfkompis" / "fixtures"
    fake_profile = Profile.model_validate(
        json.loads((fixtures_dir / "profile.json").read_text())
    )

    fake_mingolf = MagicMock(spec=MinGolf)
    fake_mingolf.fetch_profile.return_value = fake_profile

    async with LifespanManager(app):
        # Install override inside lifespan so lifespan override doesn't clobber it
        app.dependency_overrides[get_authenticated_client] = lambda: fake_mingolf  # type: ignore[assignment]
        try:
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                await _register_and_login(client, "linked@test.com", "password123")
                with patch("golfkompis.mingolf.MinGolf.login"):
                    r = await client.patch(
                        "/users/me/mingolf",
                        json={
                            "mingolf_username": "123456-789",
                            "mingolf_password": "mypass",
                        },
                    )
                assert r.status_code == 200
                r = await client.get("/api/v1/profile")
        finally:
            app.dependency_overrides.pop(get_authenticated_client, None)

    # The important check: we didn't get 412 (creds were found) and not 401 (session ok).
    assert r.status_code != 412, f"got 412: {r.json()}"
    assert r.status_code != 401, f"got 401: {r.json()}"
    assert r.status_code == 200
