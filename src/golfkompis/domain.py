from pydantic import BaseModel, Field
from datetime import datetime
from typing import List
import os
from typing import Optional, Dict

clubs_path = os.path.join(os.path.dirname(__file__), "./resources/clubs.json")


class Course(BaseModel):
    ClubID: str
    ClubName: str
    CourseID: str
    CourseName: str
    IsNineHoleCourse: bool


class GolfClub(BaseModel):
    ClubID: str
    ClubName: str | None
    Courses: List[Course] | None


class TeeSlot(BaseModel):
    golf_course: Course
    time: datetime
    current_sizr: int


# class Player(BaseModel):
#     id: str = Field(
#         max_length=9,
#         min_length=9,
#         pattern=r"^\d{6}-\d{3}$",
#         title="The ID of the Player",
#         examples=["900922-023"],
#     )
#
#
# Cancelation


class CancelBooking(BaseModel):
    Deleted: bool
    ErrorMessage: Optional[str]


# Booked


# class Booking(BaseModel):
#     HasErrors: bool
#     ErrorMessage: Optional[str]
#     NewPlayerCount: Optional[int]
#

# Below is for bookings


class SlotReservation(BaseModel):
    ID: str
    Name: str


class Slot(BaseModel):
    CourseID: str
    CourseName: str
    MaximumNumberOfSlotBookingsPerSlot: int
    OrganizationalunitID: str
    OrganizationalunitName: str
    SlotID: str
    SlotTime: str  # If you need to convert this to a datetime, you can customize it using Pydantic's datetime parsing
    Status: int
    FlexColor: int
    CreditValue: Optional[int] = None
    BookingCode: Optional[str] = None
    SlotReservations: Optional[List[SlotReservation]] = None


class Participant(BaseModel):
    ExactHcp: str
    Gender: int
    IsNineHoleBooking: bool


class PriceForHour(BaseModel):
    Price: int


class PriceDetails(BaseModel):
    MorningStart: str
    MorningEnd: str
    MorningPrice: int
    PrenoonStart: str
    PrenoonEnd: str
    PrenoonPrice: int
    AfternoonStart: str
    AfternoonEnd: str
    AfternoonPrice: int
    EveningStart: str
    EveningEnd: str
    EveningPrice: int
    PricesForHour: List[PriceForHour]


class CourseInfo(BaseModel):
    BookingInformation: str
    IsNineHoleCourse: bool
    NoShowInformation: Optional[str]


class ReceiptInfo(BaseModel):
    Email: Optional[str] = None
    Phone: Optional[str] = None
    PostalAddress: Optional[str] = None
    PostalCode: Optional[str] = None


class Slots(BaseModel):
    CourseInfo: CourseInfo
    ReceiptInfo: ReceiptInfo
    Slots: List[Slot]
    Participants: Dict[str, List[Participant]]
    Price374: Optional[PriceDetails]
    FlexContemporaryBookings: Optional[str] = None
