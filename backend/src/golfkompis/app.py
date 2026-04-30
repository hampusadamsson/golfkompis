"""FastAPI app for golfkompis - tee time search."""

import hashlib
import threading
import time as _time
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from datetime import date, time, timedelta
from importlib.metadata import version
from pathlib import Path
from typing import Annotated

import requests
import structlog
from fastapi import Depends, FastAPI, Header, HTTPException, Query, Request
from fastapi.responses import FileResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from golfkompis import smart_filters
from golfkompis.config import settings
from golfkompis.course import Courses, load_courses
from golfkompis.domain import Booking, Course, FriendOverview, Profile, Slot
from golfkompis.logging import configure_logging
from golfkompis.mingolf import BookingNotFound, CancelConflict, MinGolf

_AUTH_HEADER_NOTE = (
    "Credentials authenticate against MinGolf on first use; the resulting session "
    "is cached server-side for ~30 minutes (configurable via SESSION_TTL_MINUTES). "
    "Deploy behind TLS; no HTTPS enforcement is built in."
)

_ERROR_RESPONSES: dict[int | str, dict[str, object]] = {
    401: {"description": "Invalid or rejected MinGolf credentials"},
    502: {"description": "Upstream MinGolf API error or network failure"},
}

_BOOKING_WRITE_RESPONSES: dict[int | str, dict[str, object]] = {
    **_ERROR_RESPONSES,
    409: {"description": "Booking conflict (slot already taken or state mismatch)"},
}


# ---------------------------------------------------------------------------
# Session cache
# ---------------------------------------------------------------------------


@dataclass
class _CachedClient:
    client: MinGolf
    created_at: float


class SessionCache:
    """Thread-safe TTL cache of authenticated MinGolf instances keyed by credential hash.

    Each cached entry owns its own ``requests.Session``, so sessions are
    isolated between users. Instances are *not* individually locked — the
    underlying ``requests.Session`` is documented as not thread-safe, so two
    concurrent requests from the same user sharing one cached instance may
    interleave. In practice this is safe for the simple GET/POST calls made
    here, but callers should be aware of the limitation.
    """

    def __init__(self, ttl_seconds: float, max_entries: int) -> None:
        self._ttl = ttl_seconds
        self._max = max_entries
        self._entries: dict[str, _CachedClient] = {}
        self._lock = threading.Lock()

    @staticmethod
    def _key(username: str, password: str) -> str:
        return hashlib.sha256(f"{username}\0{password}".encode()).hexdigest()

    def get_or_login(self, username: str, password: str) -> MinGolf:
        """Return a ready authenticated client, logging in only when needed.

        Parameters
        ----------
        username:
            Golf-ID (``YYMMDD-XXX``).
        password:
            MinGolf password.

        Raises
        ------
        ValueError
            If MinGolf rejects the credentials.
        requests.HTTPError
            On non-2xx HTTP response during login.
        """
        key = self._key(username, password)
        now = _time.monotonic()
        with self._lock:
            entry = self._entries.get(key)
            if entry is not None and (now - entry.created_at) < self._ttl:
                return entry.client

        # Login outside the global lock so unrelated users aren't blocked.
        client = MinGolf()
        client.login(username, password)

        with self._lock:
            self._evict_locked(now)
            self._entries[key] = _CachedClient(client=client, created_at=now)
        return client

    def _evict_locked(self, now: float) -> None:
        """Remove expired entries; if still over cap, drop oldest. Must hold _lock."""
        self._entries = {
            k: v for k, v in self._entries.items() if (now - v.created_at) < self._ttl
        }
        if len(self._entries) >= self._max:
            oldest_key = min(self._entries, key=lambda k: self._entries[k].created_at)
            del self._entries[oldest_key]

    def close_all(self) -> None:
        """Close all cached sessions and clear the cache."""
        with self._lock:
            for entry in self._entries.values():
                entry.client.session.close()
            self._entries.clear()

    def __len__(self) -> int:
        with self._lock:
            return len(self._entries)


# ---------------------------------------------------------------------------
# Typed app state
# ---------------------------------------------------------------------------


@dataclass
class AppState:
    courses: Courses = field(default_factory=lambda: Courses(courses=[]))
    session_cache: SessionCache = field(
        default_factory=lambda: SessionCache(ttl_seconds=0, max_entries=0)
    )


# ---------------------------------------------------------------------------
# Lifespan
# ---------------------------------------------------------------------------


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    configure_logging(json_output=True)
    state = AppState(
        courses=load_courses(),
        session_cache=SessionCache(
            ttl_seconds=settings.session_ttl_minutes * 60,
            max_entries=settings.session_cache_max,
        ),
    )
    app.state.app_state = state

    if settings.mock:
        from golfkompis.mock_client import FakeMinGolf

        log = structlog.get_logger()  # pyright: ignore[reportAny]
        fake = FakeMinGolf()
        fake.preload()
        app.dependency_overrides[get_authenticated_client] = lambda: fake
        log.info("mock mode enabled — returning fixture data, auth bypassed")  # pyright: ignore[reportAny]

    yield
    state.session_cache.close_all()


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------

app = FastAPI(
    title="golfkompis",
    description=(
        "Unofficial HTTP wrapper around [MinGolf](https://mingolf.golf.se) — "
        "the Swedish golf-club booking system. "
        f"{_AUTH_HEADER_NOTE}"
    ),
    version=version("golfkompis"),
    lifespan=lifespan,
)


# ---------------------------------------------------------------------------
# Exception handlers
# ---------------------------------------------------------------------------


@app.exception_handler(requests.HTTPError)
async def http_error_handler(
    _request: Request, exc: requests.HTTPError
) -> JSONResponse:
    """Map upstream HTTP errors to appropriate status codes.

    Parameters
    ----------
    _request:
        The incoming FastAPI request (unused).
    exc:
        The ``requests.HTTPError`` raised by the MinGolf client.

    Returns
    -------
    JSONResponse
        4xx mirrors the upstream status for client-side errors;
        everything else maps to 502.
    """
    response = exc.response
    if response is not None:
        upstream = response.status_code
        if upstream == 401 or upstream == 403:
            return JSONResponse(
                status_code=401,
                content={"detail": "MinGolf rejected credentials"},
            )
        if upstream == 404:
            return JSONResponse(
                status_code=404,
                content={"detail": f"MinGolf resource not found: {exc}"},
            )
        if upstream == 409:
            return JSONResponse(
                status_code=409,
                content={"detail": f"MinGolf booking conflict: {exc}"},
            )
        if upstream == 429:
            resp = JSONResponse(
                status_code=429,
                content={"detail": "MinGolf rate limit exceeded"},
            )
            retry_after = response.headers.get("Retry-After")
            if retry_after:
                resp.headers["Retry-After"] = retry_after
            return resp
        if 400 <= upstream < 500:
            return JSONResponse(
                status_code=400,
                content={"detail": f"Invalid request to MinGolf: {exc}"},
            )
    return JSONResponse(
        status_code=502,
        content={"detail": f"MinGolf API error: {exc}"},
    )


@app.exception_handler(requests.RequestException)
async def request_exception_handler(
    _request: Request, exc: requests.RequestException
) -> JSONResponse:
    """Catch all other requests errors (timeout, connection failure, etc.).

    Parameters
    ----------
    _request:
        The incoming FastAPI request (unused).
    exc:
        Any ``requests.RequestException`` not already handled.

    Returns
    -------
    JSONResponse
        Always 502.
    """
    return JSONResponse(
        status_code=502,
        content={"detail": f"MinGolf upstream unreachable: {exc}"},
    )


# ---------------------------------------------------------------------------
# Dependencies
# ---------------------------------------------------------------------------


def get_courses(request: Request) -> Courses:
    """Return the loaded course catalogue from app state.

    Parameters
    ----------
    request:
        The incoming FastAPI request used to access ``app.state``.

    Returns
    -------
    Courses
        Parsed courses catalogue loaded at startup.
    """
    state: AppState = request.app.state.app_state
    return state.courses


CourseCatalogue = Annotated[Courses, Depends(get_courses)]


def get_authenticated_client(
    request: Request,
    x_mingolf_username: str = Header(..., alias="X-Mingolf-Username"),
    x_mingolf_password: str = Header(..., alias="X-Mingolf-Password"),
) -> MinGolf:
    """Return an authenticated MinGolf client, reusing a cached session when available.

    The session is cached server-side for ``SESSION_TTL_MINUTES`` minutes
    (default 30). Login is only called on cache miss or TTL expiry.

    Parameters
    ----------
    request:
        The incoming FastAPI request used to access the session cache.
    x_mingolf_username:
        Golf-ID in ``YYMMDD-XXX`` format, passed via ``X-Mingolf-Username`` header.
    x_mingolf_password:
        MinGolf password, passed via ``X-Mingolf-Password`` header.

    Returns
    -------
    MinGolf
        Authenticated MinGolf client instance.

    Raises
    ------
    HTTPException
        ``401`` if credentials are rejected by MinGolf.
        ``502`` if the MinGolf API returns an HTTP error during login.
    """
    state: AppState = request.app.state.app_state
    try:
        return state.session_cache.get_or_login(x_mingolf_username, x_mingolf_password)
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e)) from e
    except requests.HTTPError as e:
        raise HTTPException(status_code=502, detail=f"MinGolf API error: {e}") from e


GolfClient = Annotated[MinGolf, Depends(get_authenticated_client)]


# ---------------------------------------------------------------------------
# Request / response bodies
# ---------------------------------------------------------------------------


class HealthResponse(BaseModel):
    status: str = "ok"


class BookingRequest(BaseModel):
    slot_id: str = Field(
        ..., min_length=1, description="Tee-slot UUID from /booking/find"
    )


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@app.get(
    "/health",
    tags=["meta"],
    summary="Liveness probe",
    response_model=HealthResponse,
)
def health() -> HealthResponse:
    """Return service liveness status.

    Returns
    -------
    HealthResponse
        Always ``{"status": "ok"}`` while the service is running.
    """
    return HealthResponse()


@app.get(
    "/api/v1/booking/find",
    tags=["bookings"],
    summary="Search available tee times",
    response_model=list[Slot],
    responses={
        **_ERROR_RESPONSES,
        404: {
            "description": "One or more course UUIDs not found in the local catalogue"
        },
    },
)
def find(
    golf: GolfClient,
    courses_cat: CourseCatalogue,
    date: date = Query(..., examples=["2025-07-24"]),
    start: time | None = Query(None, examples=["07:30"]),
    stop: time | None = Query(None, examples=["12:00"]),
    spots: int = Query(1, ge=1, examples=[4]),
    courses: list[str] = Query(
        ..., max_length=50, examples=[["98369cac-d4bb-4671-931f-db10201ba1a5"]]
    ),
) -> list[Slot]:
    """Search available tee slots across one or more courses.

    Results are filtered to the requested time window and minimum party size.
    Slot times are returned in Europe/Stockholm local time.

    Parameters
    ----------
    golf:
        Authenticated MinGolf client (injected via ``X-Mingolf-*`` headers).
    courses_cat:
        Local course catalogue (injected from app state).
    date:
        Calendar date to search, e.g. ``2025-07-24``.
    start:
        Earliest acceptable tee time (inclusive). Omit for no lower bound.
    stop:
        Latest acceptable tee time (inclusive). Omit for no upper bound.
    spots:
        Minimum number of available spots required. Defaults to 1.
    courses:
        List of course UUIDs (``CourseID`` from ``/course/search``).
        Maximum 50 courses per request.

    Returns
    -------
    list[Slot]
        Available slots matching all criteria, sorted by time.

    Raises
    ------
    HTTPException
        ``404`` if any course UUID is not in the bundled catalogue.
        ``401`` if credentials are invalid.
        ``502`` on upstream MinGolf errors.
    """
    try:
        courses_list = [courses_cat.get_uuid(uuid) for uuid in courses]
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e

    schedule = golf.find_available_slots(courses_list, date)
    return smart_filters.filter_schedules(schedule, start, stop, spots)


@app.post(
    "/api/v1/booking",
    tags=["bookings"],
    summary="Book a tee time",
    status_code=204,
    response_class=Response,
    responses=_BOOKING_WRITE_RESPONSES,
)
def book(golf: GolfClient, body: BookingRequest) -> None:
    """Book a tee slot by slot ID.

    Parameters
    ----------
    golf:
        Authenticated MinGolf client (injected via ``X-Mingolf-*`` headers).
    body:
        Request body containing ``slot_id`` (UUID from ``/booking/find``).

    Returns
    -------
    None
        HTTP 204 No Content on success.

    Raises
    ------
    HTTPException
        ``409`` if the slot is already taken or a booking conflict occurs.
        ``401`` if credentials are invalid.
        ``502`` on upstream MinGolf errors.
    """
    try:
        golf.book_teetime(body.slot_id)
    except requests.HTTPError as e:
        if e.response is not None and 400 <= e.response.status_code < 500:
            raise HTTPException(status_code=409, detail=f"Booking conflict: {e}") from e
        raise


@app.get(
    "/api/v1/bookings",
    tags=["bookings"],
    summary="List upcoming bookings",
    response_model=list[Booking],
    responses=_ERROR_RESPONSES,
)
def bookings(
    golf: GolfClient,
    from_: date | None = Query(None, alias="from", examples=["2025-07-01"]),
    to: date | None = Query(None, examples=["2026-07-01"]),
) -> list[Booking]:
    """List the authenticated user's upcoming tee-time bookings.

    Parameters
    ----------
    golf:
        Authenticated MinGolf client (injected via ``X-Mingolf-*`` headers).
    from_:
        Start of the date range (inclusive). Defaults to today.
    to:
        End of the date range (inclusive).
        Defaults to today + ``settings.default_range_weeks``.

    Returns
    -------
    list[Booking]
        Upcoming bookings within the requested range.

    Raises
    ------
    HTTPException
        ``400`` if ``from`` is later than ``to``.
        ``401`` if credentials are invalid.
        ``502`` on upstream MinGolf errors.
    """
    from_date = from_ or date.today()
    to_date = to or (date.today() + timedelta(weeks=settings.default_range_weeks))
    if from_date > to_date:
        raise HTTPException(
            status_code=400, detail="`from` must not be later than `to`"
        )
    return golf.fetch_bookings(from_date, to_date)


@app.delete(
    "/api/v1/bookings/{booking_id}",
    tags=["bookings"],
    summary="Cancel a booking",
    status_code=204,
    response_class=Response,
    responses={
        **_BOOKING_WRITE_RESPONSES,
        404: {"description": "Booking not found in the upcoming 10-week window"},
    },
)
def cancel(golf: GolfClient, booking_id: str) -> None:
    """Cancel an upcoming booking by booking ID.

    Only the requesting user's own booking entry is cancelled. Group bookings
    require each player to cancel their own entry separately.

    .. note::
        The lookup window is the next 10 weeks. Bookings further out
        cannot be cancelled via this endpoint.

    Parameters
    ----------
    golf:
        Authenticated MinGolf client (injected via ``X-Mingolf-*`` headers).
    booking_id:
        Booking UUID (``Booking.bookingInfo.bookingId`` from ``/bookings``).

    Returns
    -------
    None
        HTTP 204 No Content on success.

    Raises
    ------
    HTTPException
        ``404`` if no booking with that ID exists in the upcoming 10 weeks.
        ``409`` if the booking exists in the calendar but not in the slot view
        (state mismatch — retry or contact support).
        ``401`` if credentials are invalid.
        ``502`` on upstream MinGolf errors.
    """
    try:
        golf.cancel_booking(booking_id)
    except BookingNotFound as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except CancelConflict as e:
        raise HTTPException(status_code=409, detail=str(e)) from e


@app.get(
    "/api/v1/history",
    tags=["history"],
    summary="List played rounds",
    response_model=list[Booking],
    responses=_ERROR_RESPONSES,
)
def history(
    golf: GolfClient,
    from_: date | None = Query(None, alias="from", examples=["2025-01-01"]),
    to: date | None = Query(None, examples=["2025-12-31"]),
) -> list[Booking]:
    """List the authenticated user's played rounds.

    Parameters
    ----------
    golf:
        Authenticated MinGolf client (injected via ``X-Mingolf-*`` headers).
    from_:
        Start of the date range (inclusive).
        Defaults to today minus ``settings.default_range_weeks``.
    to:
        End of the date range (inclusive). Defaults to today.

    Returns
    -------
    list[Booking]
        Played rounds within the requested range.

    Raises
    ------
    HTTPException
        ``400`` if ``from`` is later than ``to``.
        ``401`` if credentials are invalid.
        ``502`` on upstream MinGolf errors.
    """
    from_date = from_ or (date.today() - timedelta(weeks=settings.default_range_weeks))
    to_date = to or date.today()
    if from_date > to_date:
        raise HTTPException(
            status_code=400, detail="`from` must not be later than `to`"
        )
    return golf.fetch_calendar(from_date, to_date).playedRounds


@app.get(
    "/api/v1/course/search",
    tags=["courses"],
    summary="Search course catalogue",
    response_model=list[Course],
)
def search(
    courses_cat: CourseCatalogue,
    course: str = Query(..., min_length=2, examples=["Botkyrka"]),
    only_18: bool = Query(False, description="Only return 18-hole courses"),
    limit: int = Query(50, ge=1, le=500, description="Maximum number of results"),
) -> list[Course]:
    """Search the bundled course catalogue by club name.

    The search is case-insensitive substring matching against ``ClubName``.
    No authentication required.

    Parameters
    ----------
    courses_cat:
        Local course catalogue (injected from app state).
    course:
        Substring to match against club name (minimum 2 characters).
    only_18:
        If ``True``, exclude 9-hole courses from results.
    limit:
        Maximum number of courses to return (1-500, default 50).

    Returns
    -------
    list[Course]
        Matching courses, up to ``limit`` results.
    """
    results = courses_cat.search(course, only_18=only_18)
    return results[:limit]


@app.get(
    "/api/v1/course/list",
    tags=["courses"],
    summary="List all courses",
    response_model=list[Course],
)
def list_courses(
    courses_cat: CourseCatalogue,
    only_18: bool = Query(False, description="If true, exclude 9-hole courses."),
) -> list[Course]:
    """Return the full bundled course catalogue.

    No authentication required. The catalogue is a snapshot bundled at
    ``src/golfkompis/resources/courses.json`` and may be slightly stale.
    Returns every entry \u2014 no pagination, no limit.

    Parameters
    ----------
    courses_cat:
        Local course catalogue (injected from app state).
    only_18:
        If ``True``, exclude 9-hole courses.

    Returns
    -------
    list[Course]
        All courses in the bundled catalogue.
    """
    if only_18:
        return [c for c in courses_cat.courses if not c.IsNineHoleCourse]
    return courses_cat.courses


@app.get(
    "/api/v1/profile",
    tags=["profile"],
    summary="Fetch user profile",
    response_model=Profile,
    responses=_ERROR_RESPONSES,
)
def profile(golf: GolfClient) -> Profile:
    """Fetch the authenticated user's MinGolf profile.

    Parameters
    ----------
    golf:
        Authenticated MinGolf client (injected via ``X-Mingolf-*`` headers).

    Returns
    -------
    Profile
        Full MinGolf profile including HCP, membership clubs, and permissions.

    Raises
    ------
    HTTPException
        ``401`` if credentials are invalid.
        ``502`` on upstream MinGolf errors.
    """
    return golf.fetch_profile()


@app.get(
    "/api/v1/friends",
    tags=["friends"],
    summary="Fetch friend overview",
    response_model=FriendOverview,
    responses=_ERROR_RESPONSES,
)
def friends(golf: GolfClient) -> FriendOverview:
    """Fetch the authenticated user's friend overview.

    Returns both the user's own friend list and the reverse list
    (users who have added the authenticated user as a friend).

    Parameters
    ----------
    golf:
        Authenticated MinGolf client (injected via ``X-Mingolf-*`` headers).

    Returns
    -------
    FriendOverview
        ``friends`` (own list) and ``reversedFriends`` (followers).

    Raises
    ------
    HTTPException
        ``401`` if credentials are invalid.
        ``502`` on upstream MinGolf errors.
    """
    return golf.fetch_friends()


# ---------------------------------------------------------------------------
# SPA static file serving (no-op in local dev where static/ doesn't exist)
# ---------------------------------------------------------------------------

_STATIC_DIR = Path(__file__).resolve().parents[2] / "static"

if _STATIC_DIR.is_dir():
    app.mount("/_app", StaticFiles(directory=_STATIC_DIR / "_app"), name="_app")

    @app.get("/{full_path:path}", include_in_schema=False)
    def _spa_fallback(full_path: str) -> FileResponse:
        candidate = _STATIC_DIR / full_path
        if candidate.is_file():
            return FileResponse(candidate)
        return FileResponse(_STATIC_DIR / "index.html")
