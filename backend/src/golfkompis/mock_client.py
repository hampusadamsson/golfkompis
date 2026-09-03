"""FakeMinGolf: stateful fixture-backed stand-in for MinGolf used when MOCK=1.

Designed for the test-only dev deployment:

- **Tee-time search** generates rich, deterministic schedules for any course
  and date (tee times 05:00-20:00 Europe/Stockholm, every 20 minutes, varying
  availability and greenfee) instead of a single canned schedule.
- **Booking is stateful**: booking a slot reduces its availability, adds a
  booking to the account (``fetch_bookings`` / ``fetch_calendar``), and
  re-booking the same slot conflicts (HTTP 409-shaped error). Cancelling
  removes the booking and frees the slot.
- **State is in-memory but optionally persisted** to a JSON file
  (``MOCK_STATE_PATH``), so bookings survive process restarts. Without the
  setting (tests, local dev) state lives in memory only.

All fixture files live under ``src/golfkompis/fixtures/`` and are validated
against the domain Pydantic models at preload time, so stale fixtures fail
loudly on startup rather than at request time.
"""

import hashlib
import json
import uuid
from datetime import UTC, date, datetime, time, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import requests

from golfkompis.config import settings
from golfkompis.course import load_courses
from golfkompis.domain import (
    Booking,
    BookingInfo,
    BookingPlayer,
    Course,
    CourseSchedule,
    FriendOverview,
    GolfCalendar,
    Profile,
    Slot,
    SlotAvailability,
    SlotPrice,
)
from golfkompis.mingolf import BookingNotFound, MinGolf

_FIXTURES_DIR = Path(__file__).parent / "fixtures"

_STOCKHOLM = ZoneInfo("Europe/Stockholm")
_UTC = UTC

# Stockholm wall-clock tee-time window for generated schedules.
_FIRST_TEE = time(5, 0)
_LAST_TEE = time(20, 0)
_TEE_STEP_MINUTES = 20

_STATE_VERSION = 1


def _load(filename: str) -> str:
    return (_FIXTURES_DIR / filename).read_text()


def _seed(*parts: str) -> int:
    """Deterministic pseudo-random seed for stable generated data."""
    return int(hashlib.md5(":".join(parts).encode()).hexdigest(), 16)


class _MockState:
    """Mutable mock state, optionally persisted to a JSON file."""

    def __init__(self, path: str | None) -> None:
        self._path = Path(path) if path else None
        self.bookings: list[Booking] = []
        self.booked_slots: set[str] = set()
        if self._path is not None and self._path.exists():
            data = json.loads(self._path.read_text())
            self.bookings = [
                Booking.model_validate(b) for b in data.get("bookings", [])
            ]
            self.booked_slots = set(data.get("booked_slots", []))

    def save(self) -> None:
        if self._path is None:
            return
        payload = {
            "version": _STATE_VERSION,
            "bookings": [b.model_dump(mode="json") for b in self.bookings],
            "booked_slots": sorted(self.booked_slots),
        }
        tmp = self._path.with_suffix(".tmp")
        tmp.write_text(json.dumps(payload, indent=1))
        tmp.replace(self._path)


class FakeMinGolf(MinGolf):
    """MinGolf subclass backed by fixtures + mutable state — no HTTP calls.

    Activated automatically when ``MOCK=1`` is set. Use :func:`get_mock_client`
    in long-running processes so all callers share one state instance.
    """

    _bookings: list[Booking]
    _history: list[Booking]
    _profile: Profile
    _friends: FriendOverview
    _courses: dict[str, Course]
    _state: _MockState

    def __init__(self) -> None:
        # Skip MinGolf.__init__ to avoid creating a real requests.Session.
        # FakeMinGolf never makes HTTP calls.
        self._authenticated = True

    def preload(self) -> None:
        """Load fixtures + persisted state (validated at startup)."""
        self._profile = Profile.model_validate_json(_load("profile.json"))
        self._friends = FriendOverview.model_validate_json(_load("friends.json"))
        self._history = [
            Booking.model_validate(item) for item in json.loads(_load("history.json"))
        ]
        self._courses = {c.CourseID: c for c in load_courses().courses}

        self._state = _MockState(settings.mock_state_path)
        if self._state.bookings:
            # Persisted state wins — it reflects the user's mock actions.
            self._bookings = self._state.bookings
        else:
            self._bookings = [
                Booking.model_validate(item)
                for item in json.loads(_load("bookings.json"))
            ]
            self._state.bookings = self._bookings
            self._state.booked_slots = {b.slotId for b in self._bookings}
            self._state.save()

    # ------------------------------------------------------------------
    # Overrides
    # ------------------------------------------------------------------

    def login(self, username: str, password: str) -> None:  # type: ignore[override]
        """No-op in mock mode — credentials are not validated."""

    @staticmethod
    def _parse_slot_id(slot_id: str) -> tuple[str, str, str]:
        """Split ``mock-{courseId}-{yyyymmdd}-{HHMM}`` into its parts."""
        prefix = "mock-"
        if not slot_id.startswith(prefix):
            raise BookingNotFound(f"Unknown slot: {slot_id}")
        parts = slot_id[len(prefix) :].rsplit("-", 2)
        if len(parts) != 3 or len(parts[1]) != 8 or len(parts[2]) != 4:
            raise BookingNotFound(f"Unknown slot: {slot_id}")
        course_id, day, hhmm = parts
        if not (day.isdigit() and hhmm.isdigit()):
            raise BookingNotFound(f"Unknown slot: {slot_id}")
        return course_id, day, hhmm

    def _generate_schedule(self, course: Course, day: date) -> CourseSchedule:
        """Generate a deterministic tee-time sheet for one course and date."""
        slots: list[Slot] = []
        t = datetime.combine(day, _FIRST_TEE, tzinfo=_STOCKHOLM)
        end = datetime.combine(day, _LAST_TEE, tzinfo=_STOCKHOLM)
        day_key = day.strftime("%Y%m%d")

        while t <= end:
            hhmm = t.strftime("%H%M")
            slot_id = f"mock-{course.CourseID}-{day_key}-{hhmm}"
            seed = _seed(course.CourseID, str(day), hhmm)

            taken = seed % 5  # 0-4 seats already booked by "other players"
            locked = (seed >> 4) % 11 == 0  # ~9% of slots are blocked
            available = 4 - taken
            if slot_id in self._state.booked_slots:
                taken = 4
                available = 0

            players = [f"Player {chr(65 + i)}" for i in range(taken)]
            slots.append(
                Slot(
                    id=slot_id,
                    time=t.astimezone(_UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
                    price=SlotPrice(greenfee=300 + (seed % 31) * 10),
                    flexColor="green"
                    if available >= 3
                    else ("yellow" if available > 0 else "red"),
                    nineHoleBookingAavailable=False,
                    isLocked=locked,
                    availablity=SlotAvailability(
                        bookable=not locked and available > 0,
                        maxNumberOfSlotBookings=4,
                        numbersOfSlotBookings=taken,
                        numberOfBlockedRows=0,
                        numberOfNineHoleSlotBookings=0,
                        availableSlots=available,
                    ),
                    playersInfo=players,
                    reservationIds=[],
                    startProhibitionIds=[],
                )
            )
            t += timedelta(minutes=_TEE_STEP_MINUTES)

        return CourseSchedule(
            clubId=course.ClubID,
            clubName=course.ClubName,
            courseId=course.CourseID,
            courseName=course.CourseName,
            date=str(day),
            identifyAllPlayers=False,
            slots=slots,
            reservations=[],
            startProhibitions=[],
        )

    def find_available_slots(  # type: ignore[override]
        self,
        courses: list[Course],
        day: date,
    ) -> list[CourseSchedule]:
        """Generate a tee-time sheet per requested course for ``day``.

        Tee times run 05:00-20:00 Europe/Stockholm every 20 minutes, with
        deterministic availability, greenfees and occasional locked slots.
        Slots previously booked through the mock show as fully taken.
        """
        return [self._generate_schedule(course, day) for course in courses]

    def book_teetime(self, slot_id: str) -> None:  # type: ignore[override]
        """Book a generated slot: recorded in state, availability drops.

        Raises
        ------
        BookingNotFound
            If the slot id is not a mock-generated slot.
        requests.HTTPError
            With a 409 response if the slot is already booked (the app layer
            maps this to HTTP 409 conflict).
        """
        course_id, day_key, hhmm = self._parse_slot_id(slot_id)
        if slot_id in self._state.booked_slots:
            response = requests.Response()
            response.status_code = 409
            raise requests.HTTPError("slot already booked in mock", response=response)

        course = self._courses.get(course_id)
        if course is None:
            raise BookingNotFound(f"Unknown course in slot: {slot_id}")

        day = datetime.strptime(day_key, "%Y%m%d").date()
        slot_time = datetime.combine(
            day,
            time(int(hhmm[:2]), int(hhmm[2:])),
            tzinfo=_STOCKHOLM,
        )
        booking = Booking(
            clubId=course.ClubID,
            clubName=course.ClubName,
            courseId=course.CourseID,
            courseName=course.CourseName,
            slotId=slot_id,
            slotTime=slot_time.isoformat(),
            slotTimeAsDate=str(day),
            bookingInfo=BookingInfo(
                bookingId=f"mock-booking-{uuid.uuid4().hex[:8]}",
                players=[
                    BookingPlayer(
                        hcp="12.4",
                        gender="M",
                        personId=self._profile.personId,
                        name=f"{self._profile.firstName} {self._profile.lastName}",
                    )
                ],
                hcpResult=None,
                points=None,
            ),
            roundType="golf",
        )
        self._bookings.append(booking)
        self._state.booked_slots.add(slot_id)
        self._state.save()

    def cancel_booking(self, booking_id: str) -> None:  # type: ignore[override]
        """Remove a mock booking; the slot's availability is restored.

        Raises
        ------
        BookingNotFound
            If no mock booking with that id exists.
        """
        for i, booking in enumerate(self._bookings):
            info = booking.bookingInfo
            if info is not None and info.bookingId == booking_id:
                del self._bookings[i]
                self._state.booked_slots.discard(booking.slotId)
                self._state.save()
                return
        raise BookingNotFound(f"No mock booking with id: {booking_id}")

    def fetch_bookings(  # type: ignore[override]
        self,
        from_date: date,
        to_date: date,
    ) -> list[Booking]:
        """Return seeded + booked tee times within the range, soonest first."""
        return sorted(
            (
                b
                for b in self._bookings
                if from_date.isoformat() <= b.slotTimeAsDate <= to_date.isoformat()
            ),
            key=lambda b: b.slotTime,
        )

    def fetch_calendar(  # type: ignore[override]
        self,
        from_date: date,
        to_date: date,
    ) -> GolfCalendar:
        """GolfCalendar: future rounds from live bookings, past from history."""
        return GolfCalendar(
            futureRounds=self.fetch_bookings(from_date, to_date),
            playedRounds=self._history,
            lastHcpRound=None,
            isAdminForGroupBooking=False,
        )

    def fetch_profile(self) -> Profile:  # type: ignore[override]
        """Return the canned profile fixture ("Mock Player", 750101-001)."""
        return self._profile

    def fetch_friends(self) -> FriendOverview:  # type: ignore[override]
        """Return the canned friends fixture."""
        return self._friends


_shared_client: FakeMinGolf | None = None


def get_mock_client() -> FakeMinGolf:
    """Return the process-wide FakeMinGolf instance (created once, preloaded).

    The app and the queue worker must share one instance so booked state and
    persisted state stay consistent across callers.
    """
    global _shared_client
    if _shared_client is None:
        _shared_client = FakeMinGolf()
        _shared_client.preload()
    return _shared_client
