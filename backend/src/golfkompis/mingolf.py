import secrets
import string
import time as _time
from datetime import date, timedelta

import requests
import structlog

from golfkompis.config import settings
from golfkompis.domain import (
    Booking,
    Course,
    CourseSchedule,
    FriendOverview,
    GolfCalendar,
    GolfClub,
    Profile,
    SlotBookingsView,
)
from golfkompis.endpoints import (
    GET_CLUB_INFORMATION,
    GET_COURSE_SCHEDULE,
    GET_FRIEND_OVERVIEW,
    GET_GOLF_CALENDAR,
    GET_PROFILE,
    LOGIN_URL,
    SLOT_BOOKINGS,
    SLOT_LOCK,
)

log = structlog.get_logger()  # pyright: ignore[reportAny]

DEFAULT_TIMEOUT = 30  # seconds

# MinGolf's API requires a browser-like User-Agent; requests with Python's default
# UA are rejected with 403. This UA string was observed to work in production.
_MINGOLF_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/83.0.4103.97 Safari/537.36"
)


class BookingNotFound(LookupError):
    """Raised when a booking_id is not present in the user's upcoming calendar."""


class CancelConflict(RuntimeError):
    """Raised when a booking_id cannot be located in the slot bookings view."""


def _default_headers() -> dict[str, str]:
    return {
        "User-Agent": _MINGOLF_USER_AGENT,
        "Content-Type": "application/json; charset=utf-8",
    }


class MinGolf:
    """Client for the MinGolf API.

    Not thread-safe. The underlying ``requests.Session`` may interleave
    header/cookie state if a single instance is used concurrently from
    multiple threads. Each authenticated user should own a separate instance.
    """

    def __init__(self, session: requests.Session | None = None) -> None:
        self.session = session or requests.Session()
        self.session.headers.update(_default_headers())
        self._authenticated: bool = False

    def _require_login(self) -> None:
        """Raise RuntimeError if not logged in."""
        if not self._authenticated:
            raise RuntimeError(
                "not authenticated - call login() before making API requests"
            )

    def login(self, username: str, password: str) -> None:
        """Login to MinGolf. Must be called once before any API requests that require auth.

        Parameters
        ----------
        username:
            Golf-ID for mingolf.se (format: YYMMDD-XXX).
        password:
            Password for mingolf.se.

        Raises
        ------
        requests.HTTPError
            If the server returns a non-2xx status code.
        ValueError
            If login succeeds at HTTP level but the credentials are rejected.
        """
        payload = {"GolfId": username, "Password": password}
        r = self.session.post(LOGIN_URL, json=payload, timeout=DEFAULT_TIMEOUT)
        r.raise_for_status()
        body: object = r.json()  # pyright: ignore[reportAny]
        if not isinstance(body, dict) or not body.get("accessToken", False):  # pyright: ignore[reportUnknownMemberType]
            raise ValueError(
                f"MinGolf login rejected: {body.get('Message', 'unknown error') if isinstance(body, dict) else body}"  # pyright: ignore[reportUnknownMemberType]
            )
        self._authenticated = True

    def fetch_course_schedule(self, course: Course, date: date) -> CourseSchedule:
        """Fetch the full course schedule for a given course and date.

        Returns all slots (available and unavailable). Use `find_available_slots`
        to filter down to bookable slots.

        Parameters
        ----------
        course:
            Course to fetch the schedule for.
        date:
            Date for which to fetch the schedule.

        Raises
        ------
        requests.HTTPError
            On non-2xx HTTP response.
        """
        # TODO: add Sweetspot support
        self._require_login()
        url = GET_COURSE_SCHEDULE.format(club_id=course.ClubID)
        params = {
            "courseId": course.CourseID,
            "date": date.isoformat(),
        }
        r = self.session.get(url, params=params, timeout=DEFAULT_TIMEOUT)
        r.raise_for_status()
        return CourseSchedule.model_validate(r.json())

    def fetch_clubinfo(self, club_id: str) -> GolfClub:
        """Fetch club information by club ID.

        Parameters
        ----------
        club_id:
            The club's UUID.

        Raises
        ------
        requests.HTTPError
            On non-2xx HTTP response.
        """
        url = f"{GET_CLUB_INFORMATION}/{club_id}"
        r = self.session.get(url, timeout=DEFAULT_TIMEOUT)
        r.raise_for_status()
        return GolfClub.model_validate(r.json())

    def find_available_slots(
        self,
        courses: list[Course],
        date: date,
    ) -> list[CourseSchedule]:
        """Find available tee times across one or more courses. Requires login.

        Parameters
        ----------
        courses:
            Courses to search.
        date:
            Date to search.
        min_spots:
            Minimum number of available spots required in a slot (default 4).
        start_time:
            Earliest acceptable tee-off time in Stockholm local time (inclusive).
        stop_time:
            Latest acceptable tee-off time in Stockholm local time (inclusive).
        """
        self._require_login()
        log.info(
            "finding_available_slots",
            courses=[c.CourseName for c in courses],
            date=date.isoformat(),
        )

        result: list[CourseSchedule] = []
        for course in courses:
            schedule = self.fetch_course_schedule(course, date)
            result.append(schedule)
        return result

    def book_teetime(self, slot_id: str) -> None:
        """Book the given slot for the logged-in user.

        Flow:
          1. POST /Slot/{slot_id}/Lock  — acquire server-side lock.
          2. POST /Slot/{slot_id}/Bookings — commit the booking.

        The Validate step is currently skipped.
        TODO: add POST /Slot/{slot_id}/Bookings/Validate between lock and book.

        TODO: multi-player support.
        Change signature to:
            book_teetime(self, slot_id: str, friends: list[Friend] | None = None) -> None
        Then call:
            payload = self._build_booking_payload(profile, friends or [])
        The booker (profile) stays createdNumber=1, isBooker=True. Each friend
        becomes an additional list entry with createdNumber=2,3,... and
        isBooker=False. Friends are fetched via fetch_friends() (FriendOverview)
        and selected by the caller; do not auto-include all friends.

        Parameters
        ----------
        slot_id:
            UUID of the slot to book (Slot.id).

        Raises
        ------
        requests.HTTPError
            On any non-2xx HTTP response.
        """
        self._require_login()
        profile = self.fetch_profile()

        # Step 1: acquire lock
        lock_url = SLOT_LOCK.format(slot_id=slot_id)
        lock_r = self.session.post(lock_url, timeout=DEFAULT_TIMEOUT)
        lock_r.raise_for_status()

        # Step 2: commit booking
        payload = self._build_self_booking_payload(profile)
        book_url = SLOT_BOOKINGS.format(slot_id=slot_id)
        book_r = self.session.post(book_url, json=payload, timeout=DEFAULT_TIMEOUT)
        book_r.raise_for_status()

    @staticmethod
    def _random_8_lower_alnum() -> str:
        alphabet = string.ascii_lowercase + string.digits
        return "".join(secrets.choice(alphabet) for _ in range(8))

    def _build_self_booking_payload(self, profile: Profile) -> list[dict[str, object]]:
        """Build the Bookings POST payload for the logged-in user only.

        Notes
        -----
        - hashId is assumed to equal personId; this is observed empirically but
          not documented in the API.
        - hasBeenValidated is set to True to match the expected API shape even
          though the Validate step is currently skipped.
          TODO: set to False (or run Validate) once that step is implemented.
        """
        slot_booking_id = (
            f"new_{int(_time.time() * 1000)}_{self._random_8_lower_alnum()}"
        )
        player: dict[str, object] = {
            "personId": profile.personId,
            "golfId": profile.golfId,
            "firstName": profile.firstName,
            "lastName": profile.lastName,
            "fullName": f"{profile.firstName} {profile.lastName}",
            "hcp": profile.hcp,
            "age": profile.age,
            "gender": profile.gender,
            "isBooker": True,
            "homeClub": profile.homeClubName,
            "isGuest": False,
            # assumption: hashId == personId (observed in live booking trace)
            "hashId": profile.personId,
        }
        booker_entry: dict[str, object] = {
            "slotBookingId": slot_booking_id,
            "state": "Added",
            "hasBeenValidated": True,
            "player": player,
            "isNineHole": False,
            "hasArrived": False,
            "createdNumber": 1,
        }

        # TODO: multi-player extension.
        # Rename this method to `_build_booking_payload(profile, friends)` and
        # append one entry per friend after the booker entry, e.g.:
        #
        #     entries: list[dict[str, object]] = [booker_entry]
        #     for i, f in enumerate(friends, start=2):
        #         entries.append({
        #             "slotBookingId": f"new_{int(_time.time() * 1000)}_{self._random_8_lower_alnum()}",
        #             "state": "Added",
        #             "hasBeenValidated": True,
        #             "player": {
        #                 "personId": f.personId,
        #                 "golfId": f.golfId,
        #                 "firstName": f.firstName,
        #                 "lastName": f.lastName,
        #                 "fullName": f.fullName,
        #                 "hcp": f.hcp,
        #                 "age": f.age,
        #                 "gender": f.gender,
        #                 "isBooker": False,
        #                 "homeClub": f.homeClub,
        #                 "isGuest": f.isGuest,
        #                 "hashId": f.personId,  # assumption: hashId == personId
        #             },
        #             "isNineHole": False,
        #             "hasArrived": False,
        #             "createdNumber": i,
        #         })
        #     return entries
        #
        # Note: each entry needs its own unique slotBookingId.
        # Note: guests (isGuest=True) may require additional fields not present
        # on the Friend model -- verify against a real multi-player trace.
        return [booker_entry]

    def fetch_calendar(self, from_date: date, to_date: date) -> GolfCalendar:
        """Fetch the user's golf calendar (future + played rounds). Requires login.

        Parameters
        ----------
        from_date:
            Start of the date range (inclusive).
        to_date:
            End of the date range (inclusive).

        Raises
        ------
        requests.HTTPError
            On non-2xx HTTP response.
        """
        params = {"from": from_date.isoformat(), "to": to_date.isoformat()}
        self._require_login()
        r = self.session.get(GET_GOLF_CALENDAR, params=params, timeout=DEFAULT_TIMEOUT)
        r.raise_for_status()
        return GolfCalendar.model_validate(r.json())

    def fetch_bookings(self, from_date: date, to_date: date) -> list[Booking]:
        """Fetch all upcoming bookings for the logged-in user in [from_date, to_date].

        Convenience wrapper around ``fetch_calendar`` that returns only ``futureRounds``.

        Parameters
        ----------
        from_date:
            Start of the date range (inclusive).
        to_date:
            End of the date range (inclusive).

        Raises
        ------
        requests.HTTPError
            On non-2xx HTTP response.
        """
        return self.fetch_calendar(from_date, to_date).futureRounds

    def fetch_slot_bookings(
        self,
        slot_id: str,
        club_id: str,
        course_id: str,
        slot_date: date,
    ) -> SlotBookingsView:
        """Fetch the full slot bookings view for a given slot. Requires login.

        Parameters
        ----------
        slot_id:
            UUID of the slot.
        club_id:
            UUID of the club that owns the slot.
        course_id:
            UUID of the course.
        slot_date:
            Date of the slot (used as query parameter).

        Raises
        ------
        requests.HTTPError
            On non-2xx HTTP response.
        """
        url = SLOT_BOOKINGS.format(slot_id=slot_id)
        self._require_login()
        params = {
            "clubId": club_id,
            "courseId": course_id,
            "date": slot_date.isoformat(),
        }
        r = self.session.get(url, params=params, timeout=DEFAULT_TIMEOUT)
        r.raise_for_status()
        return SlotBookingsView.model_validate(r.json())

    def cancel_booking(self, booking_id: str) -> None:
        """Cancel an upcoming booking by booking id. Requires login.

        Flow:
          1. Locate the booking in the user's calendar to resolve slot_id,
             club_id, course_id, and slot date.
          2. GET /Slot/{slot_id}/Bookings?... to fetch the rich slot booking
             entry matching booking_id.
          3. POST /Slot/{slot_id}/Lock to acquire server-side lock.
          4. Mutate state -> "Deleted" and hasBeenValidated -> True, then POST
             the entry back to /Slot/{slot_id}/Bookings.

        Note: only the entry matching booking_id is deleted. If the booking
        contains multiple players (group booking), each player entry has its
        own bookingId and would need to be cancelled separately. A full group
        cancel is not yet implemented.

        Parameters
        ----------
        booking_id:
            Booking UUID (``Booking.bookingInfo.bookingId``).

        Raises
        ------
        BookingNotFound
            If no upcoming booking matches ``booking_id``.
        CancelConflict
            If the slot bookings view does not contain the expected entry.
        requests.HTTPError
            On non-2xx HTTP response.
        """
        self._require_login()
        today = date.today()
        bookings = self.fetch_bookings(
            today, today + timedelta(weeks=settings.default_range_weeks)
        )
        booking = next(
            (
                b
                for b in bookings
                if b.bookingInfo and b.bookingInfo.bookingId == booking_id
            ),
            None,
        )
        if booking is None:
            raise BookingNotFound(
                f"booking {booking_id} not found in upcoming bookings"
            )

        slot_date = date.fromisoformat(booking.slotTimeAsDate[:10])
        view = self.fetch_slot_bookings(
            booking.slotId, booking.clubId, booking.courseId, slot_date
        )
        entry = next(
            (sb for sb in view.slotBookings if sb.bookingId == booking_id), None
        )
        if entry is None:
            raise CancelConflict(
                f"booking {booking_id} not present in slot bookings view"
            )

        # Lock
        lock_url = SLOT_LOCK.format(slot_id=booking.slotId)
        lock_r = self.session.post(lock_url, timeout=DEFAULT_TIMEOUT)
        lock_r.raise_for_status()

        # Build delete payload by round-tripping the fetched entry.
        # Empty sub-objects (gameRight.sellingOrganization, purchaseTerms) are
        # echoed back as-is from the GET response — the server accepted this
        # in observed traces.
        payload_entry = entry.model_dump(exclude_none=True)
        payload_entry["state"] = "Deleted"
        payload_entry["hasBeenValidated"] = True
        # assumption: hashId == personId (same as book_teetime; observed in
        # live cancel trace). Skip if the server rejects and revisit.
        payload_entry["player"]["hashId"] = entry.player.personId

        url = SLOT_BOOKINGS.format(slot_id=booking.slotId)
        r = self.session.post(url, json=[payload_entry], timeout=DEFAULT_TIMEOUT)
        r.raise_for_status()

    def fetch_profile(self) -> Profile:
        """Fetch the logged-in user's profile. Requires login.

        Raises
        ------
        requests.HTTPError
            On non-2xx HTTP response (e.g. 401 if not logged in).
        """
        self._require_login()
        r = self.session.get(GET_PROFILE, timeout=DEFAULT_TIMEOUT)
        r.raise_for_status()
        return Profile.model_validate(r.json())

    def fetch_friends(self) -> FriendOverview:
        """Fetch the user's friend overview (friends + reverse-listed friends). Requires login.

        `friends` are people you've added.
        `reversedFriends` are people who've added you.

        Raises
        ------
        requests.HTTPError
            On non-2xx HTTP response (e.g. 401 if not logged in).
        """
        self._require_login()
        r = self.session.get(GET_FRIEND_OVERVIEW, timeout=DEFAULT_TIMEOUT)
        r.raise_for_status()
        return FriendOverview.model_validate(r.json())
