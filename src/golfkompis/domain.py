import os

from pydantic import BaseModel

clubs_path = os.path.join(os.path.dirname(__file__), "./resources/clubs.json")


# ---------------------------------------------------------------------------
# Course / Club (used for local course lookup from courses.json)
# ---------------------------------------------------------------------------


class Course(BaseModel):
    ClubID: str
    ClubName: str
    CourseID: str
    CourseName: str
    IsNineHoleCourse: bool


class GolfClub(BaseModel):
    ClubID: str
    ClubName: str | None
    Courses: list[Course] | None


# ---------------------------------------------------------------------------
# MinGolf v2 API models (CourseSchedule endpoint)
# ---------------------------------------------------------------------------


class SlotAvailability(BaseModel):
    bookable: bool
    maxNumberOfSlotBookings: int
    numbersOfSlotBookings: int
    numberOfBlockedRows: int
    numberOfNineHoleSlotBookings: int
    availableSlots: int


class SlotPrice(BaseModel):
    greenfee: int | None = None


class Slot(BaseModel):
    id: str
    time: str  # ISO datetime e.g. "2026-04-21T06:00:00"
    price: SlotPrice
    flexColor: str
    nineHoleBookingAavailable: bool  # typo matches API spec
    isLocked: bool
    availablity: SlotAvailability  # typo matches API spec
    playersInfo: list
    reservationIds: list[str]
    startProhibitionIds: list[str]
    maximumHcpPerSlot: str | None = None


class Reservation(BaseModel):
    id: str
    name: str
    note: str


class CourseSchedule(BaseModel):
    clubId: str
    clubName: str
    courseName: str
    date: str
    identifyAllPlayers: bool
    slots: list[Slot]
    reservations: list[Reservation]
    startProhibitions: list
    courseId: str | None = None
    courseTypeId: str | None = None
    sweetspotData: dict | None = None
