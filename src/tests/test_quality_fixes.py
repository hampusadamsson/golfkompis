"""Tests for smart_filters, Courses, and FastAPI app via TestClient."""

from __future__ import annotations

import json
from collections.abc import Generator
from datetime import time
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from golfkompis.course import Courses
from golfkompis.domain import CourseSchedule, Slot, SlotAvailability, SlotPrice
from golfkompis.smart_filters import filter_eligible_slots, filter_schedules

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_slot(
    *,
    slot_time: str = "2026-07-01T07:00:00Z",
    bookable: bool = True,
    is_locked: bool = False,
    available_slots: int = 4,
) -> Slot:
    return Slot(
        id="test-slot-id",
        time=slot_time,
        price=SlotPrice(),
        flexColor="",
        nineHoleBookingAavailable=False,
        isLocked=is_locked,
        availablity=SlotAvailability(
            bookable=bookable,
            maxNumberOfSlotBookings=4,
            numbersOfSlotBookings=0,
            numberOfBlockedRows=0,
            numberOfNineHoleSlotBookings=0,
            availableSlots=available_slots,
        ),
        playersInfo=[],
        reservationIds=[],
        startProhibitionIds=[],
    )


def _make_schedule(slots: list[Slot]) -> CourseSchedule:
    return CourseSchedule(
        clubId="club-1",
        date="2026-07-01",
        identifyAllPlayers=False,
        slots=slots,
        reservations=[],
        startProhibitions=[],
    )


# ---------------------------------------------------------------------------
# filter_eligible_slots
# ---------------------------------------------------------------------------


class TestFilterEligibleSlots:
    def test_bookable_slot_included(self) -> None:
        schedule = _make_schedule([_make_slot()])
        result = filter_eligible_slots(schedule, min_spots=4)
        assert len(result) == 1

    def test_non_bookable_excluded(self) -> None:
        schedule = _make_schedule([_make_slot(bookable=False)])
        result = filter_eligible_slots(schedule)
        assert result == []

    def test_locked_excluded(self) -> None:
        schedule = _make_schedule([_make_slot(is_locked=True)])
        result = filter_eligible_slots(schedule)
        assert result == []

    def test_insufficient_spots_excluded(self) -> None:
        schedule = _make_schedule([_make_slot(available_slots=2)])
        result = filter_eligible_slots(schedule, min_spots=4)
        assert result == []

    def test_start_time_boundary_inclusive(self) -> None:
        # 07:00 UTC = 09:00 Stockholm (CEST, UTC+2)
        schedule = _make_schedule([_make_slot(slot_time="2026-07-01T07:00:00Z")])
        assert filter_eligible_slots(schedule, start_time=time(9, 0)) != []
        assert filter_eligible_slots(schedule, start_time=time(9, 1)) == []

    def test_stop_time_boundary_inclusive(self) -> None:
        schedule = _make_schedule([_make_slot(slot_time="2026-07-01T07:00:00Z")])
        assert filter_eligible_slots(schedule, stop_time=time(9, 0)) != []
        assert filter_eligible_slots(schedule, stop_time=time(8, 59)) == []

    def test_no_time_bounds_returns_all_eligible(self) -> None:
        slots = [
            _make_slot(slot_time="2026-07-01T05:00:00Z"),
            _make_slot(slot_time="2026-07-01T12:00:00Z"),
        ]
        result = filter_eligible_slots(_make_schedule(slots), min_spots=1)
        assert len(result) == 2

    def test_naive_time_treated_as_utc(self) -> None:
        # Naive ISO string (no Z) — should be treated as UTC.
        # 07:00 naive = 09:00 Stockholm
        schedule = _make_schedule([_make_slot(slot_time="2026-07-01T07:00:00")])
        assert filter_eligible_slots(schedule, start_time=time(9, 0)) != []


# ---------------------------------------------------------------------------
# filter_schedules
# ---------------------------------------------------------------------------


class TestFilterSchedules:
    def test_flattens_multiple_schedules(self) -> None:
        s1 = _make_schedule([_make_slot(slot_time="2026-07-01T06:00:00Z")])
        s2 = _make_schedule([_make_slot(slot_time="2026-07-01T08:00:00Z")])
        result = filter_schedules([s1, s2], None, None, 1)
        assert len(result) == 2

    def test_empty_input(self) -> None:
        assert filter_schedules([], None, None, 1) == []

    def test_applies_time_filter_across_schedules(self) -> None:
        s1 = _make_schedule(
            [_make_slot(slot_time="2026-07-01T05:00:00Z")]
        )  # 07:00 CEST
        s2 = _make_schedule(
            [_make_slot(slot_time="2026-07-01T10:00:00Z")]
        )  # 12:00 CEST
        # 07:00 CEST < 08:00 start → excluded; 12:00 CEST > 10:00 stop → excluded
        result = filter_schedules([s1, s2], time(8, 0), time(10, 0), 1)
        assert result == []

    def test_applies_time_filter_matches(self) -> None:
        s1 = _make_schedule(
            [_make_slot(slot_time="2026-07-01T07:00:00Z")]
        )  # 09:00 CEST
        result = filter_schedules([s1], time(8, 0), time(10, 0), 1)
        assert len(result) == 1


# ---------------------------------------------------------------------------
# Courses
# ---------------------------------------------------------------------------


class TestCourses:
    @pytest.fixture
    def courses_json(self, tmp_path: Path) -> Path:
        data = {
            "courses": [
                {
                    "ClubID": "club-1",
                    "ClubName": "Botkyrka GK",
                    "CourseID": "course-1",
                    "CourseName": "Botkyrka",
                    "IsNineHoleCourse": False,
                },
                {
                    "ClubID": "club-2",
                    "ClubName": "Haninge GK",
                    "CourseID": "course-2",
                    "CourseName": "Haninge",
                    "IsNineHoleCourse": True,
                },
                {
                    "ClubID": "club-3",
                    "ClubName": "Botkyrka Pitch & Putt",
                    "CourseID": "course-3",
                    "CourseName": "Pitch & Putt",
                    "IsNineHoleCourse": True,
                },
            ]
        }
        p = tmp_path / "courses.json"
        p.write_text(json.dumps(data))
        return p

    def test_search_case_insensitive(self, courses_json: Path) -> None:
        from golfkompis.course import load_courses

        courses = load_courses(courses_json)
        result = courses.search("botkyrka")
        assert len(result) == 2

    def test_search_only_18(self, courses_json: Path) -> None:
        from golfkompis.course import load_courses

        courses = load_courses(courses_json)
        result = courses.search("botkyrka", only_18=True)
        assert len(result) == 1
        assert result[0].CourseID == "course-1"

    def test_search_no_match(self, courses_json: Path) -> None:
        from golfkompis.course import load_courses

        courses = load_courses(courses_json)
        assert courses.search("nonexistent") == []

    def test_get_uuid_found(self, courses_json: Path) -> None:
        from golfkompis.course import load_courses

        courses = load_courses(courses_json)
        course = courses.get_uuid("course-1")
        assert course.ClubName == "Botkyrka GK"

    def test_get_uuid_case_insensitive(self, courses_json: Path) -> None:
        from golfkompis.course import load_courses

        courses = load_courses(courses_json)
        course = courses.get_uuid("COURSE-1")
        assert course.CourseID == "course-1"

    def test_get_uuid_not_found_raises_key_error(self, courses_json: Path) -> None:
        from golfkompis.course import load_courses

        courses = load_courses(courses_json)
        with pytest.raises(KeyError, match="no such course"):
            courses.get_uuid("does-not-exist")

    def test_save_atomic(self, courses_json: Path, tmp_path: Path) -> None:
        from golfkompis.course import Courses, load_courses

        courses = load_courses(courses_json)
        out = tmp_path / "out.json"
        courses.save(out)
        loaded = Courses.model_validate_json(out.read_text())
        assert len(loaded.courses) == len(courses.courses)


# ---------------------------------------------------------------------------
# FastAPI TestClient (MOCK=1)
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def client() -> Generator[TestClient]:
    # Patch settings.mock before the app module is used. We do this via
    # FastAPI's dependency_overrides on the already-imported app object so
    # we avoid re-importing the module with side effects.
    from golfkompis.app import AppState, get_authenticated_client, get_courses
    from golfkompis.app import app as fastapi_app
    from golfkompis.course import load_courses as _load_courses
    from golfkompis.mock_client import FakeMinGolf

    fake = FakeMinGolf()
    fake.preload()

    def _fake_client() -> FakeMinGolf:
        return fake

    def _fake_courses() -> Courses:
        return _load_courses()

    fastapi_app.dependency_overrides[get_authenticated_client] = _fake_client
    fastapi_app.dependency_overrides[get_courses] = _fake_courses
    # Also seed app.state so get_courses fallback path works
    fastapi_app.state.app_state = AppState(
        courses=_load_courses(), http_session=__import__("requests").Session()
    )
    with TestClient(fastapi_app, raise_server_exceptions=True) as c:
        yield c
    fastapi_app.dependency_overrides.clear()


class TestAppHealthEndpoint:
    def test_health(self, client: TestClient) -> None:
        resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.json() == {"status": "ok"}


class TestAppFindEndpoint:
    def test_find_returns_list(self, client: TestClient) -> None:
        # With MOCK=1 credentials are ignored; pick any valid course UUID from fixtures
        from golfkompis.course import load_courses

        courses = load_courses()
        uuid = courses.courses[0].CourseID
        resp = client.get(
            "/api/v1/booking/find",
            params={"date": "2026-07-01", "courses": uuid},
            headers={"X-Mingolf-Username": "dummy", "X-Mingolf-Password": "dummy"},
        )
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_find_missing_courses_param_422(self, client: TestClient) -> None:
        resp = client.get(
            "/api/v1/booking/find",
            params={"date": "2026-07-01"},
            headers={"X-Mingolf-Username": "dummy", "X-Mingolf-Password": "dummy"},
        )
        assert resp.status_code == 422

    def test_find_unknown_uuid_404(self, client: TestClient) -> None:
        resp = client.get(
            "/api/v1/booking/find",
            params={
                "date": "2026-07-01",
                "courses": "00000000-0000-0000-0000-000000000000",
            },
            headers={"X-Mingolf-Username": "dummy", "X-Mingolf-Password": "dummy"},
        )
        assert resp.status_code == 404


class TestAppBookingsEndpoint:
    def test_bookings_returns_list(self, client: TestClient) -> None:
        resp = client.get(
            "/api/v1/bookings",
            headers={"X-Mingolf-Username": "dummy", "X-Mingolf-Password": "dummy"},
        )
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_bookings_from_after_to_400(self, client: TestClient) -> None:
        resp = client.get(
            "/api/v1/bookings",
            params={"from": "2027-01-01", "to": "2026-01-01"},
            headers={"X-Mingolf-Username": "dummy", "X-Mingolf-Password": "dummy"},
        )
        assert resp.status_code == 400


class TestAppCourseSearch:
    def test_course_search_no_auth_required(self, client: TestClient) -> None:
        resp = client.get("/api/v1/course/search", params={"course": "GK"})
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_course_list_no_auth_required(self, client: TestClient) -> None:
        resp = client.get("/api/v1/course/list")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)
