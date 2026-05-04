from __future__ import annotations

import asyncio
import contextlib
import json
from datetime import UTC, datetime
from zoneinfo import ZoneInfo

import structlog
from sqlalchemy import select

from golfkompis.config import settings
from golfkompis.course import load_courses
from golfkompis.domain import Slot
from golfkompis.mingolf import MinGolf
from golfkompis.queue.email import send_queue_expired_email, send_queue_match_email
from golfkompis.queue.models import QueueStatus, TeeTimeQueueEntry
from golfkompis.users.db import (
    _async_session_maker,  # pyright: ignore[reportPrivateUsage]
)
from golfkompis.users.models import User

_STOCKHOLM = ZoneInfo("Europe/Stockholm")
log = structlog.get_logger()  # pyright: ignore[reportAny]


async def run_queue_worker(stop_event: asyncio.Event) -> None:
    """Main worker loop. Polls the queue until stop_event is set."""
    interval_secs = settings.queue_poll_interval_minutes * 60
    while not stop_event.is_set():
        try:
            await _tick()
        except Exception:
            log.exception("queue_worker_tick_error")
        with contextlib.suppress(TimeoutError):
            await asyncio.wait_for(stop_event.wait(), timeout=interval_secs)


async def _tick() -> None:
    now_stockholm = datetime.now(_STOCKHOLM)
    current_time = now_stockholm.time()
    if not (
        settings.queue_active_window_start
        <= current_time
        <= settings.queue_active_window_stop
    ):
        log.debug("queue_worker_outside_active_window", current_time=current_time)
        return

    async with _async_session_maker() as session:
        result = await session.execute(
            select(TeeTimeQueueEntry).where(
                TeeTimeQueueEntry.status == QueueStatus.active
            )
        )
        entries = list(result.scalars().all())

    for entry in entries:
        try:
            await _process_entry(entry)
        except Exception:
            log.exception("queue_worker_process_entry_error", entry_id=entry.id)


def _is_expired(entry: TeeTimeQueueEntry, now_stockholm: datetime) -> bool:
    today = now_stockholm.date()
    if entry.target_date < today:
        return True
    if entry.target_date == today and entry.stop_time is not None:
        return now_stockholm.time() > entry.stop_time
    return False


async def _process_entry(entry: TeeTimeQueueEntry) -> None:
    now_stockholm = datetime.now(_STOCKHOLM)

    # Load user first since we need email for both expired and matched paths
    async with _async_session_maker() as session:
        user = await session.get(User, entry.user_id)

    if user is None:
        log.warning(
            "queue_entry_user_not_found", entry_id=entry.id, user_id=entry.user_id
        )
        return

    if _is_expired(entry, now_stockholm):
        await _resolve_expired(entry, user.email)
        return

    if not user.mingolf_username or not user.mingolf_password:
        log.warning(
            "queue_entry_user_no_credentials", entry_id=entry.id, user_id=entry.user_id
        )
        return

    mingolf_username = user.mingolf_username
    mingolf_password = user.mingolf_password

    try:
        golf = await asyncio.to_thread(_login_sync, mingolf_username, mingolf_password)
        slots = await asyncio.to_thread(_run_search_sync, golf, entry)
    except Exception:
        log.exception("queue_entry_search_error", entry_id=entry.id)
        # Still update check stats
        async with _async_session_maker() as session:
            db_entry = await session.get(TeeTimeQueueEntry, entry.id)
            if db_entry is not None:
                db_entry.last_checked_at = datetime.now(UTC)
                db_entry.check_count += 1
                session.add(db_entry)
                await session.commit()
        return

    async with _async_session_maker() as session:
        db_entry = await session.get(TeeTimeQueueEntry, entry.id)
        if db_entry is None:
            return
        db_entry.last_checked_at = datetime.now(UTC)
        db_entry.check_count += 1
        session.add(db_entry)
        await session.commit()

    if slots:
        await _resolve_matched(entry, slots, user.email)


def _login_sync(username: str, password: str) -> MinGolf:
    golf = MinGolf()
    golf.login(username, password)
    return golf


def _run_search_sync(golf: MinGolf, entry: TeeTimeQueueEntry) -> list[Slot]:
    from golfkompis import smart_filters

    courses_cat = load_courses()
    courses = [courses_cat.get_uuid(cid) for cid in entry.course_ids]
    schedule = golf.find_available_slots(courses, entry.target_date)
    return smart_filters.filter_schedules(
        schedule, entry.start_time, entry.stop_time, entry.min_spots
    )


async def _resolve_matched(
    entry: TeeTimeQueueEntry, slots: list[Slot], email: str
) -> None:
    async with _async_session_maker() as session:
        db_entry = await session.get(TeeTimeQueueEntry, entry.id)
        if db_entry is None:
            return
        db_entry.status = QueueStatus.matched
        db_entry.resolved_at = datetime.now(UTC)
        db_entry.matched_slots_json = json.dumps(
            [s.model_dump() for s in slots[: settings.queue_email_max_slots]]
        )
        session.add(db_entry)
        await session.commit()

    await send_queue_match_email(email, entry, slots, settings.queue_email_max_slots)


async def _resolve_expired(entry: TeeTimeQueueEntry, email: str) -> None:
    async with _async_session_maker() as session:
        db_entry = await session.get(TeeTimeQueueEntry, entry.id)
        if db_entry is None:
            return
        db_entry.status = QueueStatus.expired
        db_entry.resolved_at = datetime.now(UTC)
        session.add(db_entry)
        await session.commit()

    await send_queue_expired_email(email, entry)
