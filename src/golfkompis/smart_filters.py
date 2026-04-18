from datetime import datetime, time
from zoneinfo import ZoneInfo

from golfkompis.domain import CourseSchedule, Slot

_UTC = ZoneInfo("UTC")
_STOCKHOLM = ZoneInfo("Europe/Stockholm")


def filter_eligible_slots(
    schedule: CourseSchedule,
    min_spots: int = 4,
    start_time: time | None = None,
    stop_time: time | None = None,
) -> list[Slot]:
    """Filter a CourseSchedule down to bookable, available slots.

    Slot times from the API are in UTC (Z) and are converted to
    Europe/Stockholm before comparing against start_time and stop_time.

    Parameters
    ----------
    schedule:
        The full course schedule returned by the MinGolf API.
    min_spots:
        Minimum number of available spots required in a slot (default 4).
    start_time:
        Earliest acceptable tee-off time in Stockholm local time (inclusive).
        None means no lower bound.
    stop_time:
        Latest acceptable tee-off time in Stockholm local time (inclusive).
        None means no upper bound.

    Returns
    -------
    list[Slot]
        Slots that are bookable, not locked, have enough available spots,
        and fall within the requested time window.
    """

    def eligible(slot: Slot) -> bool:
        if not slot.availablity.bookable:
            return False
        if slot.isLocked:
            return False
        if slot.availablity.availableSlots < min_spots:
            return False
        dt = (
            datetime.fromisoformat(slot.time)
            .replace(tzinfo=_UTC)
            .astimezone(_STOCKHOLM)
        )
        slot_time = dt.time()
        if start_time is not None and slot_time < start_time:
            return False
        return stop_time is None or slot_time <= stop_time

    return [slot for slot in schedule.slots if eligible(slot)]
