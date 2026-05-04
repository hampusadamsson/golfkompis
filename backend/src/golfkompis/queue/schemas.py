from __future__ import annotations

import json
import uuid
from datetime import date, datetime, time

from pydantic import BaseModel, Field, model_validator

from golfkompis.domain import Slot
from golfkompis.queue.models import QueueStatus, TeeTimeQueueEntry


class QueueEntryCreate(BaseModel):
    target_date: date
    start_time: time | None = None
    stop_time: time | None = None
    min_spots: int = Field(1, ge=1, le=4)
    course_ids: list[str] = Field(..., min_length=1, max_length=50)

    @model_validator(mode="after")
    def _validate_times(self) -> QueueEntryCreate:
        if self.start_time and self.stop_time and self.start_time >= self.stop_time:
            raise ValueError("start_time must be before stop_time")
        return self


class QueueEntryUpdate(BaseModel):
    start_time: time | None = None
    stop_time: time | None = None
    min_spots: int | None = Field(None, ge=1, le=4)
    course_ids: list[str] | None = Field(None, min_length=1, max_length=50)

    @model_validator(mode="after")
    def _validate_times(self) -> QueueEntryUpdate:
        if self.start_time and self.stop_time and self.start_time >= self.stop_time:
            raise ValueError("start_time must be before stop_time")
        return self


class QueueEntryRead(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    target_date: date
    start_time: time | None
    stop_time: time | None
    min_spots: int
    course_ids: list[str]
    status: QueueStatus
    created_at: datetime
    last_checked_at: datetime | None
    check_count: int
    resolved_at: datetime | None
    matched_slots: list[Slot] | None = None

    @model_validator(mode="before")
    @classmethod
    def _parse_json_fields(cls, data: object) -> object:
        # When constructing from an ORM instance, unwrap the JSON fields
        if isinstance(data, TeeTimeQueueEntry):
            matched: list[Slot] | None = None
            if data.matched_slots_json:
                matched = [
                    Slot.model_validate(s) for s in json.loads(data.matched_slots_json)
                ]
            return {
                "id": data.id,
                "target_date": data.target_date,
                "start_time": data.start_time,
                "stop_time": data.stop_time,
                "min_spots": data.min_spots,
                "course_ids": data.course_ids,
                "status": data.status,
                "created_at": data.created_at,
                "last_checked_at": data.last_checked_at,
                "check_count": data.check_count,
                "resolved_at": data.resolved_at,
                "matched_slots": matched,
            }
        return data
