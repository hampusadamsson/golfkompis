"""FastAPI app for golfkompis - tee time search."""

from datetime import date, time, timedelta
from typing import Annotated

import requests
import uvicorn
from fastapi import Depends, FastAPI, Header, HTTPException, Query, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from golfkompis import smart_filters
from golfkompis.course import load_courses
from golfkompis.domain import Booking, FriendOverview, Profile
from golfkompis.mingolf import MinGolf

app = FastAPI()

_courses = load_courses()

DEFAULT_RANGE_WEEKS = 10


# ---------------------------------------------------------------------------
# Exception handler
# ---------------------------------------------------------------------------


@app.exception_handler(requests.HTTPError)
async def http_error_handler(
    _request: Request, exc: requests.HTTPError
) -> JSONResponse:
    return JSONResponse(
        status_code=502,
        content={"detail": f"MinGolf API error: {exc}"},
    )


# ---------------------------------------------------------------------------
# Dependency
# ---------------------------------------------------------------------------


def get_authenticated_client(
    x_mingolf_username: str = Header(..., alias="X-Mingolf-Username"),
    x_mingolf_password: str = Header(..., alias="X-Mingolf-Password"),
) -> MinGolf:
    """Authenticate and return a ready MinGolf client."""
    golf = MinGolf()
    try:
        golf.login(x_mingolf_username, x_mingolf_password)
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e)) from e
    except requests.HTTPError as e:
        raise HTTPException(status_code=502, detail=f"MinGolf API error: {e}") from e
    return golf


GolfClient = Annotated[MinGolf, Depends(get_authenticated_client)]


# ---------------------------------------------------------------------------
# Request bodies
# ---------------------------------------------------------------------------


class BookingRequest(BaseModel):
    slot_id: str


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@app.get("/api/v1/booking/find")
def find(
    golf: GolfClient,
    date: date = Query(..., example="2025-07-24"),
    start: time = Query(..., example="07:30"),
    stop: time = Query(..., example="12:00"),
    spots: int = Query(..., example=4),
    courses: list[str] = Query(..., example=["98369cac-d4bb-4671-931f-db10201ba1a5"]),
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

    schedule = golf.find_available_slots(courses_list, date)
    return smart_filters.filter(schedule, start, stop, spots)


@app.post("/api/v1/booking", status_code=204)
def book(golf: GolfClient, body: BookingRequest):
    """Book a tee time by slot ID.

    Credentials are passed via request headers:
      X-Mingolf-Username: Golf-ID (YYMMDD-XXX)
      X-Mingolf-Password: MinGolf password
    """
    golf.book_teetime(body.slot_id)


@app.get("/api/v1/bookings", response_model=list[Booking])
def bookings(
    golf: GolfClient,
    to: date | None = Query(None, example="2026-07-01"),
):
    """List the user's upcoming bookings.

    `from` is fixed to today. `to` defaults to today + 10 weeks.

    Credentials are passed via request headers:
      X-Mingolf-Username: Golf-ID (YYMMDD-XXX)
      X-Mingolf-Password: MinGolf password
    """
    from_date = date.today()
    to_date = to or (date.today() + timedelta(weeks=DEFAULT_RANGE_WEEKS))
    return golf.fetch_bookings(from_date, to_date)


@app.delete("/api/v1/bookings/{booking_id}", status_code=204)
def cancel(golf: GolfClient, booking_id: str):
    """Cancel an upcoming booking by booking ID.

    Credentials are passed via request headers:
      X-Mingolf-Username: Golf-ID (YYMMDD-XXX)
      X-Mingolf-Password: MinGolf password
    """
    try:
        golf.cancel_booking(booking_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e


@app.get("/api/v1/history", response_model=list[Booking])
def history(
    golf: GolfClient,
    from_: date | None = Query(None, alias="from", example="2025-01-01"),
    to: date | None = Query(None, example="2025-12-31"),
):
    """List the user's played rounds.

    `from` defaults to today - 10 weeks. `to` defaults to today.

    Credentials are passed via request headers:
      X-Mingolf-Username: Golf-ID (YYMMDD-XXX)
      X-Mingolf-Password: MinGolf password
    """
    from_date = from_ or (date.today() - timedelta(weeks=DEFAULT_RANGE_WEEKS))
    to_date = to or date.today()
    return golf.fetch_calendar(from_date, to_date).playedRounds


@app.get("/api/v1/course/search")
def search(
    course: str = Query(..., example="Botkyrka"),
):
    """Search for courses by name."""
    return _courses.search(course)


@app.get("/api/v1/profile", response_model=Profile)
def profile(golf: GolfClient):
    """Fetch the logged-in user's MinGolf profile.

    Credentials are passed via request headers:
      X-Mingolf-Username: Golf-ID (YYMMDD-XXX)
      X-Mingolf-Password: MinGolf password
    """
    return golf.fetch_profile()


@app.get("/api/v1/friends", response_model=FriendOverview)
def friends(golf: GolfClient):
    """Fetch the user's friend overview (friends + reverse-listed friends).

    Credentials are passed via request headers:
      X-Mingolf-Username: Golf-ID (YYMMDD-XXX)
      X-Mingolf-Password: MinGolf password
    """
    return golf.fetch_friends()


if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
