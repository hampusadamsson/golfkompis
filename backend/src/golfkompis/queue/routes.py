from __future__ import annotations

import json
import uuid
from datetime import UTC, datetime
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from golfkompis.course import Courses, load_courses
from golfkompis.queue.models import QueueStatus, TeeTimeQueueEntry
from golfkompis.queue.schemas import QueueEntryCreate, QueueEntryRead, QueueEntryUpdate
from golfkompis.users.db import get_async_session
from golfkompis.users.manager import current_active_user
from golfkompis.users.models import User

router = APIRouter()
_STOCKHOLM = ZoneInfo("Europe/Stockholm")


def _get_courses() -> Courses:
    return load_courses()


def _validate_course_ids(course_ids: list[str], courses: Courses) -> None:
    for cid in course_ids:
        try:
            courses.get_uuid(cid)
        except KeyError:
            raise HTTPException(
                status_code=404, detail=f"Course UUID not found: {cid}"
            ) from None


@router.get("", response_model=list[QueueEntryRead])
async def list_entries(
    status: QueueStatus = QueueStatus.active,
    user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session),
) -> list[QueueEntryRead]:
    result = await session.execute(
        select(TeeTimeQueueEntry).where(
            TeeTimeQueueEntry.user_id == user.id,
            TeeTimeQueueEntry.status == status,
        )
    )
    entries = result.scalars().all()
    return [QueueEntryRead.model_validate(e) for e in entries]


@router.post("", response_model=QueueEntryRead, status_code=201)
async def create_entry(
    body: QueueEntryCreate,
    user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session),
    courses: Courses = Depends(_get_courses),
) -> QueueEntryRead:
    if not user.mingolf_username or not user.mingolf_password:
        raise HTTPException(status_code=412, detail="mingolf_not_linked")

    today = datetime.now(_STOCKHOLM).date()
    if body.target_date < today:
        raise HTTPException(
            status_code=422, detail="target_date must be today or in the future"
        )

    _validate_course_ids(body.course_ids, courses)

    entry = TeeTimeQueueEntry(
        user_id=user.id,
        target_date=body.target_date,
        start_time=body.start_time,
        stop_time=body.stop_time,
        min_spots=body.min_spots,
        course_ids_json=json.dumps(body.course_ids),
    )
    session.add(entry)
    await session.commit()
    await session.refresh(entry)
    return QueueEntryRead.model_validate(entry)


@router.get("/{entry_id}", response_model=QueueEntryRead)
async def get_entry(
    entry_id: uuid.UUID,
    user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session),
) -> QueueEntryRead:
    entry = await session.get(TeeTimeQueueEntry, entry_id)
    if entry is None or entry.user_id != user.id:
        raise HTTPException(status_code=404, detail="Not found")
    return QueueEntryRead.model_validate(entry)


@router.patch("/{entry_id}", response_model=QueueEntryRead)
async def update_entry(
    entry_id: uuid.UUID,
    body: QueueEntryUpdate,
    user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session),
    courses: Courses = Depends(_get_courses),
) -> QueueEntryRead:
    entry = await session.get(TeeTimeQueueEntry, entry_id)
    if entry is None or entry.user_id != user.id:
        raise HTTPException(status_code=404, detail="Not found")
    if entry.status != QueueStatus.active:
        raise HTTPException(status_code=409, detail="entry is not active")

    if body.course_ids is not None:
        _validate_course_ids(body.course_ids, courses)
        entry.course_ids = body.course_ids
    if body.start_time is not None:
        entry.start_time = body.start_time
    if body.stop_time is not None:
        entry.stop_time = body.stop_time
    if body.min_spots is not None:
        entry.min_spots = body.min_spots

    session.add(entry)
    await session.commit()
    await session.refresh(entry)
    return QueueEntryRead.model_validate(entry)


@router.delete("/{entry_id}", status_code=204)
async def cancel_entry(
    entry_id: uuid.UUID,
    user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session),
) -> None:
    entry = await session.get(TeeTimeQueueEntry, entry_id)
    if entry is None or entry.user_id != user.id:
        raise HTTPException(status_code=404, detail="Not found")
    entry.status = QueueStatus.cancelled
    entry.resolved_at = datetime.now(UTC)
    session.add(entry)
    await session.commit()
