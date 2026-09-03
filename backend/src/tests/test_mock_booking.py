# pyright: reportPrivateUsage=false, reportUnknownParameterType=false, reportMissingParameterType=false, reportUnknownMemberType=false, reportUnknownArgumentType=false, reportUnknownVariableType=false
"""Tests for the stateful FakeMinGolf mock (booking, cancel, persistence)."""

from datetime import date

import pytest
import requests

from golfkompis.config import settings
from golfkompis.mingolf import BookingNotFound
from golfkompis.mock_client import FakeMinGolf


@pytest.fixture()
def fake() -> FakeMinGolf:
    client = FakeMinGolf()
    client.preload()
    return client


def _any_bookable_slot(fake: FakeMinGolf, day: date) -> tuple[str, object]:
    courses = list(fake._courses.values())
    schedule = fake._generate_schedule(courses[0], day)
    slot = next(s for s in schedule.slots if s.availablity.bookable and not s.isLocked)
    return slot.id, courses[0]


def test_generated_schedule_shape(fake: FakeMinGolf) -> None:
    day = date(2026, 9, 15)
    courses = list(fake._courses.values())
    schedules = fake.find_available_slots(courses[:3], day)
    assert len(schedules) == 3
    s = schedules[0]
    assert s.date == "2026-09-15"
    assert len(s.slots) > 40  # 05:00-20:00 every 20 min
    # deterministic across calls
    again = fake.find_available_slots(courses[:3], day)
    assert [x.id for x in again[0].slots] == [x.id for x in s.slots]


def test_slot_times_are_stockholm_wall_clock_in_utc(fake: FakeMinGolf) -> None:
    day = date(2026, 9, 15)  # CEST (UTC+2)
    courses = list(fake._courses.values())
    schedule = fake._generate_schedule(courses[0], day)
    first = min(schedule.slots, key=lambda s: s.time)
    # 05:00 Stockholm == 03:00Z in September
    assert first.time == "2026-09-15T03:00:00Z"


def test_book_adds_booking_and_fills_slot(fake: FakeMinGolf) -> None:
    day = date(2026, 9, 15)
    slot_id, _ = _any_bookable_slot(fake, day)

    fake.book_teetime(slot_id)

    bookings = fake.fetch_bookings(day, day)
    assert any(b.slotId == slot_id for b in bookings)
    booking = next(b for b in bookings if b.slotId == slot_id)
    assert booking.bookingInfo is not None
    assert booking.bookingInfo.bookingId.startswith("mock-booking-")

    # slot now fully taken in generated schedules
    course_id, _day_key, _hhmm = FakeMinGolf._parse_slot_id(slot_id)
    course = fake._courses[course_id]
    schedule = fake._generate_schedule(course, day)
    booked_slot = next(s for s in schedule.slots if s.id == slot_id)
    assert booked_slot.availablity.availableSlots == 0
    assert booked_slot.availablity.bookable is False


def test_double_booking_conflicts(fake: FakeMinGolf) -> None:
    slot_id, _ = _any_bookable_slot(fake, date(2026, 9, 16))
    fake.book_teetime(slot_id)
    with pytest.raises(requests.HTTPError) as excinfo:
        fake.book_teetime(slot_id)
    assert excinfo.value.response is not None
    assert excinfo.value.response.status_code == 409


def test_cancel_removes_booking_and_frees_slot(fake: FakeMinGolf) -> None:
    day = date(2026, 9, 17)
    slot_id, _ = _any_bookable_slot(fake, day)
    fake.book_teetime(slot_id)
    booking = next(b for b in fake.fetch_bookings(day, day) if b.slotId == slot_id)
    booking_id = booking.bookingInfo.bookingId  # type: ignore[union-attr]

    fake.cancel_booking(booking_id)

    assert all(b.slotId != slot_id for b in fake.fetch_bookings(day, day))
    course_id, _, _ = FakeMinGolf._parse_slot_id(slot_id)
    schedule = fake._generate_schedule(fake._courses[course_id], day)
    freed = next(s for s in schedule.slots if s.id == slot_id)
    assert freed.availablity.availableSlots > 0


def test_cancel_unknown_booking_raises(fake: FakeMinGolf) -> None:
    with pytest.raises(BookingNotFound):
        fake.cancel_booking("mock-booking-does-not-exist")


def test_book_unknown_slot_raises(fake: FakeMinGolf) -> None:
    with pytest.raises(BookingNotFound):
        fake.book_teetime("not-a-mock-slot")
    with pytest.raises(BookingNotFound):
        fake.book_teetime("mock-00000000-0000-0000-0000-000000000000-99999999-9999")


def test_state_persists_across_instances(tmp_path, monkeypatch) -> None:
    state_file = tmp_path / "mock-state.json"
    monkeypatch.setattr(settings, "mock_state_path", str(state_file))

    day = date(2026, 9, 18)
    first = FakeMinGolf()
    first.preload()
    slot_id, _ = _any_bookable_slot(first, day)
    first.book_teetime(slot_id)
    assert state_file.exists()

    # a fresh instance (pod restart) sees the booking
    second = FakeMinGolf()
    second.preload()
    assert any(b.slotId == slot_id for b in second.fetch_bookings(day, day))
    # and the slot stays taken
    course_id, _day_key, _hhmm = FakeMinGolf._parse_slot_id(slot_id)
    schedule = second._generate_schedule(second._courses[course_id], day)
    assert (
        next(s for s in schedule.slots if s.id == slot_id).availablity.availableSlots
        == 0
    )

    # cancelling in the new instance also persists
    booking = next(b for b in second.fetch_bookings(day, day) if b.slotId == slot_id)
    second.cancel_booking(booking.bookingInfo.bookingId)  # type: ignore[union-attr]
    third = FakeMinGolf()
    third.preload()
    assert all(b.slotId != slot_id for b in third.fetch_bookings(day, day))


def test_seeded_fixture_bookings_present_without_state(fake: FakeMinGolf) -> None:
    bookings = fake.fetch_bookings(date(2025, 1, 1), date(2027, 1, 1))
    assert any(b.slotId == "mock-slot-aaaa-0001" for b in bookings)
