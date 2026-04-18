from datetime import time
from golfkompis.domain import Slot, Slots


def filter_eligible_slots(
    slots: Slots,
    n_slots_to_look_for=4,
    start_time: time | None = None,
    stop_time: time | None = None,
) -> list[Slot]:
    return list(
        filter(
            lambda slot: slot.Status >= 0
            and (
                start_time is None
                or time.fromisoformat(slot.SlotTime[9:13]) >= start_time
            )
            and (
                stop_time is None
                or time.fromisoformat(slot.SlotTime[9:13]) <= stop_time
            )
            and not slot.SlotReservations
            and (
                slot.SlotID not in slots.Participants
                or n_slots_to_look_for <= (4 - len(slots.Participants[slot.SlotID]))
            ),
            slots.Slots,
        )
    )
