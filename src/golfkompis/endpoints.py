"""URL constants for the MinGolf API.

All constants are format strings where applicable; use `.format(...)` to
substitute path parameters before calling.
"""

_BASE = "https://mingolf.golf.se"

# --- Auth ---
LOGIN_URL = f"{_BASE}/login/api/Users/Login"

# --- Profile ---
GET_PROFILE = f"{_BASE}/login/api/profile"

# --- Club / course ---
GET_CLUB_INFORMATION = f"{_BASE}/handlers/booking/GetClubInformation"
GET_COURSE_SCHEDULE = f"{_BASE}/bokning/api/Clubs/{{club_id}}/CourseSchedule"

# --- Calendar ---
# Note: "GolfCalender" misspelling matches the actual API path.
GET_GOLF_CALENDAR = f"{_BASE}/start/api/Persons/GolfCalender"

# --- Slot ---
SLOT_BOOKINGS = f"{_BASE}/bokning/api/Slot/{{slot_id}}/Bookings"
SLOT_LOCK = f"{_BASE}/bokning/api/Slot/{{slot_id}}/Lock"

# --- Social ---
GET_FRIEND_OVERVIEW = f"{_BASE}/minainstallningar/favoriter/api/Persons/FriendOverview"
