from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi_mail import MessageSchema, MessageType, NameEmail

from golfkompis.users.email import mail_client as _fm

if TYPE_CHECKING:
    from golfkompis.domain import Slot
    from golfkompis.queue.models import TeeTimeQueueEntry


async def send_queue_match_email(
    email: str,
    entry: TeeTimeQueueEntry,
    slots: list[Slot],
    max_slots: int = 20,
) -> None:
    shown = slots[:max_slots]
    more_count = max(0, len(slots) - max_slots)
    body = {
        "target_date": entry.target_date.strftime("%Y-%m-%d"),
        "slots": [
            {
                "time": s.time,
                "available_spots": s.availablity.availableSlots,
                "price": s.price.greenfee,
            }
            for s in shown
        ],
        "more_count": more_count,
    }
    message = MessageSchema(
        subject="Lediga tider hittades — Golfkompis",
        recipients=[NameEmail(email, email)],
        template_body=body,
        subtype=MessageType.html,
    )
    await _fm.send_message(message, template_name="queue_match.html")


async def send_queue_expired_email(
    email: str,
    entry: TeeTimeQueueEntry,
) -> None:
    body = {
        "target_date": entry.target_date.strftime("%Y-%m-%d"),
        "start_time": entry.start_time.strftime("%H:%M") if entry.start_time else None,
        "stop_time": entry.stop_time.strftime("%H:%M") if entry.stop_time else None,
        "min_spots": entry.min_spots,
    }
    message = MessageSchema(
        subject="Inga lediga tider hittades — Golfkompis",
        recipients=[NameEmail(email, email)],
        template_body=body,
        subtype=MessageType.html,
    )
    await _fm.send_message(message, template_name="queue_expired.html")
