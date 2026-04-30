from typing import Any

from pydantic import BaseModel

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
    playersInfo: list[str]
    reservationIds: list[str]
    startProhibitionIds: list[str]
    maximumHcpPerSlot: str | None = None


class Reservation(BaseModel):
    id: str
    name: str
    note: str


class BookingPlayer(BaseModel):
    hcp: str
    gender: str
    personId: str | None = None
    name: str | None = None


class BookingInfo(BaseModel):
    bookingId: str
    players: list[BookingPlayer]
    hcpResult: str | None = None
    points: int | None = None


class Booking(BaseModel):
    clubId: str
    clubName: str
    courseId: str
    courseName: str
    slotId: str
    slotTime: str
    slotTimeAsDate: str
    bookingInfo: BookingInfo | None = None
    roundType: str


class GolfCalendar(BaseModel):
    futureRounds: list[Booking]
    playedRounds: list[Booking]
    lastHcpRound: str | None = None
    isAdminForGroupBooking: bool


class CourseSchedule(BaseModel):
    clubId: str
    clubName: str | None = None
    courseName: str | None = None
    date: str
    identifyAllPlayers: bool
    slots: list[Slot]
    reservations: list[Reservation]
    startProhibitions: list[Any]
    courseId: str | None = None
    courseTypeId: str | None = None
    sweetspotData: dict[str, Any] | None = None


# ---------------------------------------------------------------------------
# Profile
# ---------------------------------------------------------------------------


class MemberClub(BaseModel):
    isHomeClub: bool
    id: str
    name: str


class Profile(BaseModel):
    sessionId: str
    personId: str
    firstName: str
    lastName: str
    golfId: str
    homeClubId: str | None = None
    homeClubName: str | None = None
    districtName: str | None = None
    favouriteClubId: str | None = None
    representationClubName: str | None = None
    representationClubShort: str | None = None
    gender: str
    birthDate: str
    age: int
    hcp: str
    allowedToBook: bool
    allowedToBookWithNoCharge: bool
    allowedToCompetitionSignUp: bool
    allowedToCompetitionSignUpNoCharge: bool
    allowedToPay: bool
    emailAddress: str | None = None
    hasActiveMembership: bool
    loggedInToMinGolfThisYear: bool
    minors: list[Any]
    memberClubs: list[MemberClub]
    caregiverPersonId: str | None = None
    caregiverGolfId: str | None = None
    isMinor: bool
    isMinorWithoutCaregiver: bool
    imageUrl: str | None = None
    isDefaultSupport: bool
    isFederationSuspended: bool
    isFederationSuspendedCompetition: bool
    isMinorNotLoggedInAsCaregiver: bool
    capped: bool
    softCap: str | None = None
    hardCap: str | None = None
    lowestHcp: str | None = None
    hcpCard: str | None = None
    isSgfJunior: bool
    isMemberOfTeenTourClub: bool
    hasPaidTeenTourYearlyFee: bool
    mustChangePassword: bool
    isLoggedInWithFreja: bool
    showPersonInfoView: bool
    isForeign: bool
    country: str | None = None


# ---------------------------------------------------------------------------
# Friends
# ---------------------------------------------------------------------------


class FriendTee(BaseModel):
    saveAsDefault: bool


class Friend(BaseModel):
    personId: str
    golfId: str
    firstName: str
    lastName: str
    fullName: str
    hcp: str
    age: int
    gender: str
    isBooker: bool
    homeClub: str | None = None
    isGuest: bool
    tee: FriendTee
    country: str | None = None
    imageUrl: str | None = None


class FriendOverview(BaseModel):
    friends: list[Friend]
    reversedFriends: list[Friend]


# ---------------------------------------------------------------------------
# Slot bookings (used for cancel flow)
# ---------------------------------------------------------------------------


class SlotBookingPlayer(BaseModel):
    id: str
    personId: str
    golfId: str
    firstName: str
    lastName: str
    fullName: str
    hcp: str
    age: int
    emailAddress: str | None = None
    gender: str
    gameRight: dict[str, Any] | None = None
    articleBookings: list[Any]
    isBooker: bool
    isGuest: bool
    tee: FriendTee  # same shape: {"saveAsDefault": bool}
    country: str | None = None
    homeClub: str | None = None  # not in GET response but present in cancel POST
    hashId: str | None = None  # injected before POSTing; assumption: hashId == personId


class SlotBooking(BaseModel):
    slotBookingId: str
    createdAt: str
    createdNumber: int
    player: SlotBookingPlayer
    bookingId: str
    state: str
    hasBeenValidated: bool
    isNineHole: bool
    hasArrived: bool
    isPartOfGroupBooking: bool


class SlotBookingsView(BaseModel):
    clubId: str
    clubName: str | None = None
    courseId: str
    courseName: str | None = None
    courseIsPayAndPlay: bool
    courseIsNineHole: bool
    bookingInformation: str | None = None
    identifyAllPlayers: bool
    hasUnpaidMandatoryEngagements: bool
    slot: Slot
    mandatoryPaymentInfo: dict[str, Any]
    reservations: list[Reservation]
    startProhibitions: list[Any]
    slotBookings: list[SlotBooking]
