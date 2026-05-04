import enum
import json
import uuid
from datetime import UTC, date, datetime, time

from sqlalchemy import Date, DateTime, ForeignKey, Integer, Text, Time
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column

from golfkompis.users.db import Base


class QueueStatus(enum.StrEnum):
    active = "active"
    matched = "matched"
    expired = "expired"
    cancelled = "cancelled"


class TeeTimeQueueEntry(Base):
    __tablename__ = "tee_time_queue"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("user.id", ondelete="CASCADE"), nullable=False, index=True
    )
    target_date: Mapped[date] = mapped_column(Date, nullable=False)
    start_time: Mapped[time | None] = mapped_column(Time, nullable=True)
    stop_time: Mapped[time | None] = mapped_column(Time, nullable=True)
    min_spots: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    # JSON array of CourseID strings
    course_ids_json: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[QueueStatus] = mapped_column(
        SQLEnum(QueueStatus), nullable=False, default=QueueStatus.active, index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )
    last_checked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    check_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    resolved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    # JSON array of Slot dicts when status=matched (capped at queue_email_max_slots)
    matched_slots_json: Mapped[str | None] = mapped_column(Text, nullable=True)

    @property
    def course_ids(self) -> list[str]:
        return json.loads(self.course_ids_json)  # type: ignore[no-any-return]

    @course_ids.setter
    def course_ids(self, value: list[str]) -> None:
        self.course_ids_json = json.dumps(value)
