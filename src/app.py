"""FastAPI app for golfkompis - tee time search."""

from datetime import date, time, timedelta

import requests
import uvicorn
from fastapi import FastAPI, Header, HTTPException, Query

from golfkompis import smart_filters
from golfkompis.course import load_courses
from golfkompis.domain import Booking, FriendOverview, Profile
from golfkompis.mingolf import MinGolf

app = FastAPI()

_courses = load_courses()

DEFAULT_RANGE_WEEKS = 10


def _login(username: str, password: str) -> MinGolf:
    golf = MinGolf()
    try:
        golf.login(username, password)
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e)) from e
    except requests.HTTPError as e:
        raise HTTPException(status_code=502, detail=f"MinGolf API error: {e}") from e
    return golf


@app.get("/api/v1/booking/find")
def find(
    date: date = Query(..., example="2025-07-24"),
    start: time = Query(..., example="07:30"),
    stop: time = Query(..., example="12:00"),
    spots: int = Query(..., example=4),
    courses: list[str] = Query(..., example=["98369cac-d4bb-4671-931f-db10201ba1a5"]),
    x_mingolf_username: str = Header(..., alias="X-Mingolf-Username"),
    x_mingolf_password: str = Header(..., alias="X-Mingolf-Password"),
):
    """Get available golf tee times for the requested date and time window.

    Credentials are passed via request headers:
      X-Mingolf-Username: Golf-ID (YYMMDD-XXX)
      X-Mingolf-Password: MinGolf password

    Returns a list of available slots across the requested courses.
    """
    try:
        courses_list = [_courses.get_uuid(uuid) for uuid in courses]
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e

    golf = _login(x_mingolf_username, x_mingolf_password)

    try:
        schedule = golf.find_available_slots(courses_list, date)
        return smart_filters.filter(schedule, start, stop, spots)
    except requests.HTTPError as e:
        raise HTTPException(status_code=502, detail=f"MinGolf API error: {e}") from e


@app.get("/api/v1/bookings", response_model=list[Booking])
def bookings(
    to: date | None = Query(None, example="2026-07-01"),
    x_mingolf_username: str = Header(..., alias="X-Mingolf-Username"),
    x_mingolf_password: str = Header(..., alias="X-Mingolf-Password"),
):
    """List the user's upcoming bookings.

    `from` is fixed to today. `to` defaults to today + 10 weeks.

    Credentials are passed via request headers:
      X-Mingolf-Username: Golf-ID (YYMMDD-XXX)
      X-Mingolf-Password: MinGolf password
    """
    from_date = date.today()
    to_date = to or (date.today() + timedelta(weeks=DEFAULT_RANGE_WEEKS))

    golf = _login(x_mingolf_username, x_mingolf_password)
    try:
        return golf.fetch_bookings(from_date, to_date)
    except requests.HTTPError as e:
        raise HTTPException(status_code=502, detail=f"MinGolf API error: {e}") from e


@app.get("/api/v1/history", response_model=list[Booking])
def history(
    from_: date | None = Query(None, alias="from", example="2025-01-01"),
    to: date | None = Query(None, example="2025-12-31"),
    x_mingolf_username: str = Header(..., alias="X-Mingolf-Username"),
    x_mingolf_password: str = Header(..., alias="X-Mingolf-Password"),
):
    """List the user's played rounds.

    `from` defaults to today - 10 weeks. `to` defaults to today.

    Credentials are passed via request headers:
      X-Mingolf-Username: Golf-ID (YYMMDD-XXX)
      X-Mingolf-Password: MinGolf password
    """
    from_date = from_ or (date.today() - timedelta(weeks=DEFAULT_RANGE_WEEKS))
    to_date = to or date.today()

    golf = _login(x_mingolf_username, x_mingolf_password)
    try:
        return golf.fetch_calendar(from_date, to_date).playedRounds
    except requests.HTTPError as e:
        raise HTTPException(status_code=502, detail=f"MinGolf API error: {e}") from e


@app.get("/api/v1/course/search")
def search(
    course: str = Query(..., example="Botkyrka"),
):
    """Search for courses by name."""
    return _courses.search(course)


@app.get("/api/v1/profile", response_model=Profile)
def profile(
    x_mingolf_username: str = Header(..., alias="X-Mingolf-Username"),
    x_mingolf_password: str = Header(..., alias="X-Mingolf-Password"),
):
    """Fetch the logged-in user's MinGolf profile.

    Credentials are passed via request headers:
      X-Mingolf-Username: Golf-ID (YYMMDD-XXX)
      X-Mingolf-Password: MinGolf password
    """
    golf = _login(x_mingolf_username, x_mingolf_password)
    try:
        return golf.fetch_profile()
    except requests.HTTPError as e:
        raise HTTPException(status_code=502, detail=f"MinGolf API error: {e}") from e


@app.get("/api/v1/friends", response_model=FriendOverview)
def friends(
    x_mingolf_username: str = Header(..., alias="X-Mingolf-Username"),
    x_mingolf_password: str = Header(..., alias="X-Mingolf-Password"),
):
    """Fetch the user's friend overview (friends + reverse-listed friends).

    Credentials are passed via request headers:
      X-Mingolf-Username: Golf-ID (YYMMDD-XXX)
      X-Mingolf-Password: MinGolf password
    """
    golf = _login(x_mingolf_username, x_mingolf_password)
    try:
        return golf.fetch_friends()
    except requests.HTTPError as e:
        raise HTTPException(status_code=502, detail=f"MinGolf API error: {e}") from e


if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
