"""FakeMinGolf: canned-data stand-in for MinGolf used when MOCK=1.

All fixture files live under src/golfkompis/fixtures/ and are validated against
the domain Pydantic models at preload time, so stale fixtures fail loudly on
startup rather than at request time.
"""

import json
from datetime import date
from pathlib import Path

from golfkompis.domain import (
    Booking,
    Course,
    CourseSchedule,
    FriendOverview,
    GolfCalendar,
    Profile,
)
from golfkompis.mingolf import MinGolf

_FIXTURES_DIR = Path(__file__).parent / "fixtures"


def _load(filename: str) -> str:
    return (_FIXTURES_DIR / filename).read_text()


class FakeMinGolf(MinGolf):
    """MinGolf subclass that returns canned fixture data instead of calling MinGolf.

    Intended for local development and testing only. Activated automatically
    when ``MOCK=1`` is set.

    All write operations (``book_teetime``, ``cancel_booking``) are no-ops
    and always succeed.
    """

    _course_schedules: list[CourseSchedule]
    _bookings: list[Booking]
    _history: list[Booking]
    _profile: Profile
    _friends: FriendOverview

    def __init__(self) -> None:
        # Skip MinGolf.__init__ to avoid creating a real requests.Session.
        # FakeMinGolf never makes HTTP calls.
        self._authenticated = True

    def preload(self) -> None:
        """Eagerly load and validate all fixtures.

        Raises ``pydantic.ValidationError`` on startup if any fixture is
        invalid, rather than failing silently at request time.
        """
        self._course_schedules = [
            CourseSchedule.model_validate(item)
            for item in json.loads(_load("course_schedules.json"))
        ]
        self._bookings = [
            Booking.model_validate(item) for item in json.loads(_load("bookings.json"))
        ]
        self._history = [
            Booking.model_validate(item) for item in json.loads(_load("history.json"))
        ]
        self._profile = Profile.model_validate_json(_load("profile.json"))
        self._friends = FriendOverview.model_validate_json(_load("friends.json"))

    # ------------------------------------------------------------------
    # Overrides
    # ------------------------------------------------------------------

    def login(self, username: str, password: str) -> None:  # type: ignore[override]
        """No-op in mock mode — credentials are not validated."""

    def find_available_slots(  # type: ignore[override]
        self,
        courses: list[Course],
        date: date,
    ) -> list[CourseSchedule]:
        """Return the canned course schedules fixture.

        Parameters
        ----------
        courses:
            Ignored in mock mode.
        date:
            Ignored in mock mode.

        Returns
        -------
        list[CourseSchedule]
            Fixture data from ``fixtures/course_schedules.json``.
        """
        return self._course_schedules

    def book_teetime(self, slot_id: str) -> None:  # type: ignore[override]
        """No-op in mock mode — always succeeds."""

    def fetch_bookings(  # type: ignore[override]
        self,
        from_date: date,
        to_date: date,
    ) -> list[Booking]:
        """Return the canned bookings fixture.

        Parameters
        ----------
        from_date:
            Ignored in mock mode.
        to_date:
            Ignored in mock mode.

        Returns
        -------
        list[Booking]
            Fixture data from ``fixtures/bookings.json``.
        """
        return self._bookings

    def cancel_booking(self, booking_id: str) -> None:  # type: ignore[override]
        """No-op in mock mode — always succeeds."""

    def fetch_calendar(  # type: ignore[override]
        self,
        from_date: date,
        to_date: date,
    ) -> GolfCalendar:
        """Return a GolfCalendar built from the history fixture.

        Parameters
        ----------
        from_date:
            Ignored in mock mode.
        to_date:
            Ignored in mock mode.

        Returns
        -------
        GolfCalendar
            ``playedRounds`` populated from ``fixtures/history.json``;
            ``futureRounds`` populated from ``fixtures/bookings.json``.
        """
        return GolfCalendar(
            futureRounds=self._bookings,
            playedRounds=self._history,
            lastHcpRound=None,
            isAdminForGroupBooking=False,
        )

    def fetch_profile(self) -> Profile:  # type: ignore[override]
        """Return the canned profile fixture.

        Returns
        -------
        Profile
            Fixture data from ``fixtures/profile.json``.
        """
        return self._profile

    def fetch_friends(self) -> FriendOverview:  # type: ignore[override]
        """Return the canned friends fixture.

        Returns
        -------
        FriendOverview
            Fixture data from ``fixtures/friends.json``.
        """
        return self._friends
