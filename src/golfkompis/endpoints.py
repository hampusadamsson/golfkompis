"""URL constants for the MinGolf API.

All constants are format strings where applicable; use `.format(...)` to
substitute path parameters before calling.
"""

# --- Auth ---
LOGIN_URL = "https://mingolf.golf.se/login/api/Users/Login"

# --- Profile ---
GET_PROFILE = "https://mingolf.golf.se/login/api/profile"

# --- Club / course ---
GET_CLUB_INFORMATION = "https://mingolf.golf.se/handlers/booking/GetClubInformation"
GET_COURSE_SCHEDULE = (
    "https://mingolf.golf.se/bokning/api/Clubs/{club_id}/CourseSchedule"
)

# --- Calendar ---
# Note: "GolfCalender" misspelling matches the actual API path.
GET_GOLF_CALENDAR = "https://mingolf.golf.se/start/api/Persons/GolfCalender"

# --- Slot ---
SLOT_BOOKINGS = "https://mingolf.golf.se/bokning/api/Slot/{slot_id}/Bookings"
SLOT_LOCK = "https://mingolf.golf.se/bokning/api/Slot/{slot_id}/Lock"

# --- Social ---
GET_FRIEND_OVERVIEW = (
    "https://mingolf.golf.se/minainstallningar/favoriter/api/Persons/FriendOverview"
)
