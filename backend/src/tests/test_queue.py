"""Integration tests for the tee-time queue feature (routes + worker)."""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator
from datetime import date, time, timedelta
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
from asgi_lifespan import LifespanManager

# ---------------------------------------------------------------------------
# Real course UUID from the bundled catalogue
# ---------------------------------------------------------------------------

_REAL_COURSE_ID = "fb4af479-63e3-4728-a205-c86894d3d649"  # Allerum Golfklubb, 18-hole

# ---------------------------------------------------------------------------
# App fixture
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def anyio_backend() -> str:
    return "asyncio"


@pytest.fixture(scope="module")
async def test_app(  # pyright: ignore[reportUnknownParameterType]
    tmp_path_factory: pytest.TempPathFactory,
) -> AsyncGenerator[Any]:
    tmp = tmp_path_factory.mktemp("queue_db")
    tmp_url = f"sqlite+aiosqlite:///{tmp / 'test_queue.db'}"

    from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

    import golfkompis.users.db as users_db

    test_engine = create_async_engine(tmp_url)
    users_db._engine = test_engine  # pyright: ignore[reportPrivateUsage]
    users_db._async_session_maker = async_sessionmaker(  # pyright: ignore[reportPrivateUsage]
        test_engine, expire_on_commit=False
    )

    from golfkompis.config import settings

    settings.queue_enabled = False  # prevent background worker from running

    from golfkompis.app import app

    async with LifespanManager(app):
        yield app

    settings.queue_enabled = True  # restore


def _fresh_client(app: Any) -> httpx.AsyncClient:
    return httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),  # type: ignore[arg-type]
        base_url="http://test",
    )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _login(client: httpx.AsyncClient, email: str, password: str) -> None:
    resp = await client.post(
        "/auth/login", data={"username": email, "password": password}
    )
    assert resp.status_code == 204, resp.text


async def _register_and_login(
    client: httpx.AsyncClient, email: str, password: str
) -> None:
    with patch(
        "golfkompis.users.email.send_verification_email", new_callable=AsyncMock
    ):
        resp = await client.post(
            "/auth/register", json={"email": email, "password": password}
        )
    assert resp.status_code == 201, resp.text
    await _login(client, email, password)


async def _set_mingolf_creds(client: httpx.AsyncClient) -> None:
    with patch("golfkompis.mingolf.MinGolf.login"):
        resp = await client.patch(
            "/users/me/mingolf",
            json={"mingolf_username": "990101-001", "mingolf_password": "testpass"},
        )
    assert resp.status_code == 200, resp.text


async def _get_user_id(client: httpx.AsyncClient) -> uuid.UUID:
    resp = await client.get("/users/me")
    assert resp.status_code == 200
    return uuid.UUID(resp.json()["id"])


def _tomorrow() -> str:
    return (date.today() + timedelta(days=1)).isoformat()


def _yesterday() -> str:
    return (date.today() - timedelta(days=1)).isoformat()


async def _seed_entry(
    user_id: uuid.UUID,
    target_date: date,
    course_ids: list[str],
    stop_time: time | None = None,
    status: str = "active",
) -> Any:
    import json as _json

    from golfkompis.queue.models import QueueStatus, TeeTimeQueueEntry
    from golfkompis.users.db import (
        _async_session_maker,  # pyright: ignore[reportPrivateUsage]
    )

    entry = TeeTimeQueueEntry(
        user_id=user_id,
        target_date=target_date,
        min_spots=1,
        course_ids_json=_json.dumps(course_ids),
        status=QueueStatus(status),
    )
    if stop_time:
        entry.stop_time = stop_time

    async with _async_session_maker() as session:
        session.add(entry)
        await session.commit()
        await session.refresh(entry)
        return entry


def _make_slot() -> Any:
    from golfkompis.domain import Slot, SlotAvailability, SlotPrice

    return Slot(
        id="test-slot-1",
        time="2026-06-01T10:00:00",
        price=SlotPrice(greenfee=None),
        flexColor="green",
        nineHoleBookingAavailable=False,
        isLocked=False,
        availablity=SlotAvailability(
            bookable=True,
            maxNumberOfSlotBookings=4,
            numbersOfSlotBookings=0,
            numberOfBlockedRows=0,
            numberOfNineHoleSlotBookings=0,
            availableSlots=4,
        ),
        playersInfo=[],
        reservationIds=[],
        startProhibitionIds=[],
    )


# ---------------------------------------------------------------------------
# Test 1: CRUD happy path
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_crud_happy_path(test_app: Any) -> None:
    async with _fresh_client(test_app) as c:
        await _register_and_login(c, "crud@test.com", "password1234")
        await _set_mingolf_creds(c)

        # POST
        resp = await c.post(
            "/api/v1/queue",
            json={"target_date": _tomorrow(), "course_ids": [_REAL_COURSE_ID]},
        )
        assert resp.status_code == 201, resp.text
        body = resp.json()
        assert body["status"] == "active"
        entry_id = body["id"]

        # GET list
        resp = await c.get("/api/v1/queue")
        assert resp.status_code == 200
        ids = [e["id"] for e in resp.json()]
        assert entry_id in ids

        # GET by id
        resp = await c.get(f"/api/v1/queue/{entry_id}")
        assert resp.status_code == 200
        assert resp.json()["id"] == entry_id

        # PATCH
        resp = await c.patch(f"/api/v1/queue/{entry_id}", json={"min_spots": 2})
        assert resp.status_code == 200
        assert resp.json()["min_spots"] == 2

        # DELETE
        resp = await c.delete(f"/api/v1/queue/{entry_id}")
        assert resp.status_code == 204

        # After delete: GET by id returns 200 with status=cancelled
        resp = await c.get(f"/api/v1/queue/{entry_id}")
        assert resp.status_code == 200
        assert resp.json()["status"] == "cancelled"

        # GET list (default status=active) should NOT include cancelled entry
        resp = await c.get("/api/v1/queue")
        assert resp.status_code == 200
        ids = [e["id"] for e in resp.json()]
        assert entry_id not in ids


# ---------------------------------------------------------------------------
# Test 2: Owner isolation
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_owner_isolation(test_app: Any) -> None:
    async with _fresh_client(test_app) as user_a:
        await _register_and_login(user_a, "owner_a@test.com", "password1234")
        await _set_mingolf_creds(user_a)

        resp = await user_a.post(
            "/api/v1/queue",
            json={"target_date": _tomorrow(), "course_ids": [_REAL_COURSE_ID]},
        )
        assert resp.status_code == 201
        entry_id = resp.json()["id"]

    async with _fresh_client(test_app) as user_b:
        await _register_and_login(user_b, "owner_b@test.com", "password1234")

        resp = await user_b.get(f"/api/v1/queue/{entry_id}")
        assert resp.status_code == 404

        resp = await user_b.patch(f"/api/v1/queue/{entry_id}", json={"min_spots": 2})
        assert resp.status_code == 404

        resp = await user_b.delete(f"/api/v1/queue/{entry_id}")
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Test 3: POST validation
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_post_validation(test_app: Any) -> None:
    async with _fresh_client(test_app) as c:
        await _register_and_login(c, "valid_creds@test.com", "password1234")
        await _set_mingolf_creds(c)

        # Past date → 422
        resp = await c.post(
            "/api/v1/queue",
            json={"target_date": _yesterday(), "course_ids": [_REAL_COURSE_ID]},
        )
        assert resp.status_code == 422, resp.text

        # Invalid course UUID → 404
        bad_uuid = "00000000-0000-0000-0000-000000000000"
        resp = await c.post(
            "/api/v1/queue",
            json={"target_date": _tomorrow(), "course_ids": [bad_uuid]},
        )
        assert resp.status_code == 404, resp.text

    # Missing MinGolf creds → 412
    async with _fresh_client(test_app) as c2:
        await _register_and_login(c2, "no_creds@test.com", "password1234")
        resp = await c2.post(
            "/api/v1/queue",
            json={"target_date": _tomorrow(), "course_ids": [_REAL_COURSE_ID]},
        )
        assert resp.status_code == 412, resp.text


# ---------------------------------------------------------------------------
# Test 4: Worker tick — match path
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_worker_tick_match(test_app: Any) -> None:
    from golfkompis.queue.models import QueueStatus, TeeTimeQueueEntry
    from golfkompis.queue.worker import _tick  # pyright: ignore[reportPrivateUsage]
    from golfkompis.users.db import (
        _async_session_maker,  # pyright: ignore[reportPrivateUsage]
    )

    async with _fresh_client(test_app) as c:
        await _register_and_login(c, "worker_match@test.com", "password1234")
        await _set_mingolf_creds(c)
        user_id = await _get_user_id(c)

    entry = await _seed_entry(user_id, date.today(), [_REAL_COURSE_ID])
    slot = _make_slot()
    mock_golf = MagicMock()

    with (
        patch(
            "golfkompis.queue.worker.settings.queue_active_window_start",
            time(0, 0),
        ),
        patch(
            "golfkompis.queue.worker.settings.queue_active_window_stop",
            time(23, 59),
        ),
        patch(
            "golfkompis.queue.worker._async_session_maker",
            _async_session_maker,
        ),
        patch(
            "golfkompis.queue.worker._login_sync",
            return_value=mock_golf,
        ),
        patch(
            "golfkompis.queue.worker._run_search_sync",
            return_value=[slot],
        ),
        patch(
            "golfkompis.queue.worker.send_queue_match_email",
            new_callable=AsyncMock,
        ) as mock_email,
    ):
        await _tick()

    async with _async_session_maker() as session:
        db_entry = await session.get(TeeTimeQueueEntry, entry.id)
        assert db_entry is not None
        assert db_entry.status == QueueStatus.matched
        assert db_entry.matched_slots_json is not None
        assert db_entry.check_count == 1

    assert mock_email.called
    # At least one call should target our seeded entry
    entry_ids = [call[0][1].id for call in mock_email.call_args_list]
    assert entry.id in entry_ids


# ---------------------------------------------------------------------------
# Test 5: Worker tick — expired path
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_worker_tick_expired(test_app: Any) -> None:
    from golfkompis.queue.models import QueueStatus, TeeTimeQueueEntry
    from golfkompis.queue.worker import _tick  # pyright: ignore[reportPrivateUsage]
    from golfkompis.users.db import (
        _async_session_maker,  # pyright: ignore[reportPrivateUsage]
    )

    async with _fresh_client(test_app) as c:
        await _register_and_login(c, "worker_expired@test.com", "password1234")
        user_id = await _get_user_id(c)

    yesterday = date.today() - timedelta(days=1)
    entry = await _seed_entry(user_id, yesterday, [_REAL_COURSE_ID])

    with (
        patch(
            "golfkompis.queue.worker.settings.queue_active_window_start",
            time(0, 0),
        ),
        patch(
            "golfkompis.queue.worker.settings.queue_active_window_stop",
            time(23, 59),
        ),
        patch(
            "golfkompis.queue.worker._async_session_maker",
            _async_session_maker,
        ),
        patch(
            "golfkompis.queue.worker.send_queue_expired_email",
            new_callable=AsyncMock,
        ) as mock_expired_email,
        patch(
            "golfkompis.queue.worker._login_sync",
            side_effect=AssertionError("login should not be called for expired entry"),
        ),
    ):
        await _tick()

    async with _async_session_maker() as session:
        db_entry = await session.get(TeeTimeQueueEntry, entry.id)
        assert db_entry is not None
        assert db_entry.status == QueueStatus.expired
        assert db_entry.resolved_at is not None

    mock_expired_email.assert_called_once()


# ---------------------------------------------------------------------------
# Test 6: Worker tick — outside active window
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_worker_tick_outside_window(test_app: Any) -> None:
    from golfkompis.queue.models import QueueStatus, TeeTimeQueueEntry
    from golfkompis.queue.worker import _tick  # pyright: ignore[reportPrivateUsage]
    from golfkompis.users.db import (
        _async_session_maker,  # pyright: ignore[reportPrivateUsage]
    )

    async with _fresh_client(test_app) as c:
        await _register_and_login(c, "worker_window@test.com", "password1234")
        await _set_mingolf_creds(c)
        user_id = await _get_user_id(c)

    entry = await _seed_entry(
        user_id, date.today() + timedelta(days=2), [_REAL_COURSE_ID]
    )

    login_mock = MagicMock(
        side_effect=AssertionError("login should not be called outside window")
    )

    with (
        patch(
            "golfkompis.queue.worker.settings.queue_active_window_start",
            time(23, 0),
        ),
        patch(
            "golfkompis.queue.worker.settings.queue_active_window_stop",
            time(23, 59),
        ),
        patch("golfkompis.queue.worker._async_session_maker", _async_session_maker),
        patch("golfkompis.queue.worker._login_sync", login_mock),
    ):
        await _tick()

    async with _async_session_maker() as session:
        db_entry = await session.get(TeeTimeQueueEntry, entry.id)
        assert db_entry is not None
        assert db_entry.status == QueueStatus.active


# ---------------------------------------------------------------------------
# Test 7: Worker tick — user without MinGolf creds
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_worker_tick_no_mingolf_creds(test_app: Any) -> None:
    from golfkompis.queue.models import QueueStatus, TeeTimeQueueEntry
    from golfkompis.queue.worker import _tick  # pyright: ignore[reportPrivateUsage]
    from golfkompis.users.db import (
        _async_session_maker,  # pyright: ignore[reportPrivateUsage]
    )

    async with _fresh_client(test_app) as c:
        await _register_and_login(c, "worker_nocreds@test.com", "password1234")
        # No mingolf creds set
        user_id = await _get_user_id(c)

    entry = await _seed_entry(
        user_id, date.today() + timedelta(days=3), [_REAL_COURSE_ID]
    )

    login_mock = MagicMock(
        side_effect=AssertionError("login should not be called for user without creds")
    )

    with (
        patch(
            "golfkompis.queue.worker.settings.queue_active_window_start",
            time(0, 0),
        ),
        patch(
            "golfkompis.queue.worker.settings.queue_active_window_stop",
            time(23, 59),
        ),
        patch("golfkompis.queue.worker._async_session_maker", _async_session_maker),
        patch("golfkompis.queue.worker._login_sync", login_mock),
    ):
        await _tick()

    async with _async_session_maker() as session:
        db_entry = await session.get(TeeTimeQueueEntry, entry.id)
        assert db_entry is not None
        assert db_entry.status == QueueStatus.active
        assert db_entry.check_count == 0
