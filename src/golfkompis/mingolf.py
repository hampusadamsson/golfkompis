from datetime import date, time

import requests
import structlog

from golfkompis.course import load_courses
from golfkompis.domain import Course, CourseSchedule, GolfClub, Slot
from golfkompis.smart_filters import filter_eligible_slots

log = structlog.get_logger()  # pyright: ignore[reportAny]

LOGIN_URL = "https://mingolf.golf.se/login/api/Users/Login"
GET_CLUB_INFORMATION = "https://mingolf.golf.se/handlers/booking/GetClubInformation"
GET_COURSE_SCHEDULE = (
    "https://mingolf.golf.se/bokning/api/Clubs/{club_id}/CourseSchedule"
)

HEADERS: dict[str, str | bytes] = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.97 Safari/537.36",
    "Content-Type": "application/json; charset=utf-8",
}


class MinGolf:
    def __init__(self, session: requests.Session | None = None) -> None:
        self.session = session or requests.Session()
        self.session.headers = HEADERS
        self._courses = load_courses()

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
        r = self.session.post(LOGIN_URL, json=payload)
        r.raise_for_status()
        body = r.json()
        if isinstance(body, dict) and not body.get("IsLoggedIn", True):
            raise ValueError(
                f"MinGolf login rejected: {body.get('Message', 'unknown error')}"
            )

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
        url = GET_COURSE_SCHEDULE.format(club_id=course.ClubID)
        params = {
            "courseId": course.CourseID,
            "date": date.isoformat(),
        }
        try:
            r = self.session.get(url, params=params)
            r.raise_for_status()
            return CourseSchedule.model_validate(r.json())
        except Exception as e:
            log.error(
                "fetch_course_schedule_failed",
                url=url,
                course_id=course.CourseID,
                error=str(e),
            )
            raise

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
        r = self.session.get(url)
        r.raise_for_status()
        return GolfClub.model_validate(r.json())

    def find_available_slots(
        self,
        courses: list[Course],
        date: date,
        min_spots: int = 4,
        start_time: time | None = None,
        stop_time: time | None = None,
    ) -> list[Slot]:
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
        log.info(
            "finding_available_slots",
            courses=[c.CourseName for c in courses],
            date=date.isoformat(),
            min_spots=min_spots,
            start_time=start_time.isoformat() if start_time else None,
            stop_time=stop_time.isoformat() if stop_time else None,
        )

        result: list[Slot] = []
        for course in courses:
            schedule = self.fetch_course_schedule(course, date)
            result.extend(
                filter_eligible_slots(schedule, min_spots, start_time, stop_time)
            )
        return result

    def book_teetime(self, slot: Slot, players: list[str]) -> None:
        """Create a booking for the given slot.

        Not yet implemented.
        """
        raise NotImplementedError("book_teetime is not yet implemented")

    def fetch_bookings(self) -> list[Slot]:
        """Fetch all tee times booked by the logged-in user.

        Not yet implemented.
        """
        raise NotImplementedError("fetch_bookings is not yet implemented")

    def cancel_booking(self, slot: Slot) -> None:
        """Cancel a booking.

        Not yet implemented.
        """
        raise NotImplementedError("cancel_booking is not yet implemented")
