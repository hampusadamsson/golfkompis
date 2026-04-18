'''
from datetime import date, time from golfkompis.course import load_courses from golfkompis.mingolf import MinGolf

golf = MinGolf()
golf_courses = golf.search_courses("Botkyrka") # [0]
print(golf_courses)
golf.login("900921-017", "088594")
spots = golf.search_free_slots(
course=golf_courses,
date=date.fromisoformat("20250728"),
n_slots_to_look_for=4,
start_time=time(hour=8),
stop_time=time(hour=15),
)
for t in spots:
print(t.SlotTime, t.CourseName, t.CourseID)

reservation = golf.book_teetime(spots[0], [])
print(reservation)
cb = golf.cancel_booking(spots[0])
assert cb.Deleted, cb.ErrorMessage
'''

'''
from golfkompis.domain import Slot
from golfkompis.mingolf import MinGolf

golf = MinGolf()
spots = Slot.model_construct(
SlotID="9712a4f1-5235-4ffd-be5b-ae2feecd0797",
SlotTime="20250720T080000",
CourseID="4bfc39cf-b2d2-4a32-ba81-a8db53e59bb2",
ClubID="4fb14a3a-2135-4ae8-a302-0f7a38c93567",
bookingCode="",
MaximumNumberOfSlotBookingsPerSlot=1,
OrganizationalunitID="",
OrganizationalunitName="",
reInitOnMissingBooking=True,
failOnMissingBooking=False,
)
reservation = golf.book_teetime(spots, [])
print(reservation)
'''
