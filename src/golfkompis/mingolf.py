from datetime import date, time, datetime

from dateutil.relativedelta import relativedelta
import requests
from golfkompis.course import load_courses
from golfkompis.domain import (
    CancelBooking,
    GolfClub,
    Slot,
    Course,
    Slots,
    TeeSlot,
)
from golfkompis.smart_filters import filter_eligible_slots
import itertools

LOGIN_URL = "https://mingolf.golf.se/Login"
GET_TEETIMES = "https://mingolf.golf.se/handlers/booking/GetTeeTimesFullDay"
GET_CLUB_INFORMATION = "https://mingolf.golf.se/handlers/booking/GetClubInformation"

HEADERS: dict[str, str | bytes] = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.97 Safari/537.36"
}


class MinGolf:
    def __init__(self, session=requests.Session()) -> None:
        self.session = session
        self.session.headers = HEADERS
        self.courses = load_courses()

    def login(self, username: str, password: str) -> None:
        """Login function. Any request to MinGolf should be preceded by this,
        but only once since it's stored in a session.

        Parameters
        ----------
        username: str
            username (str): Golf-id for mingolf.se YYMMDD-XXX
        password: str
            password (str): Password for mingolf.se
        """
        post_data = {
            "txtGolfID": username,
            "txtPassword": password,
            "target": LOGIN_URL,
            "action": "submit",
        }
        r = self.session.post(LOGIN_URL, data=post_data)
        if "exp-forgot-password" in str(r.content):
            raise Exception(
                "Error during login: Please check login-credentials to www.mingolf.se"
            )

    def fetch_slots(self, course: Course, date: date) -> Slots:
        """Look for slots in golf tee times. Note that these are not only available slots.

        Parameters
        ----------
        course: Course
            A course object containing clubID, courseID etc.
        date: datetime.date
            Date for which to look for open tee times (eg. 20250708)
        """
        course_id = course.CourseID
        club_id = course.ClubID
        date_str = date.strftime("%Y%m%d")
        url = f"{GET_TEETIMES}/{course_id}/{club_id}/{date_str}T000000/1"
        data = self.session.get(url).json()
        return Slots.model_validate(data)

    def fetch_clubinfo(self, club_id: str) -> GolfClub:
        """Get information about a club based on the club ID"""
        url = f"{GET_CLUB_INFORMATION}/{club_id}"
        data = self.session.get(url).json()
        return GolfClub.model_validate(data)

    def search_courses(self, name: str) -> list[Course]:
        """Search for courses by name using club name as referernce"""
        return self.courses.search(name)

    def get_courses_by_uuid(self, uuid: str) -> Course:
        """Search for courses by uuid using club name as referernce"""
        return self.courses.get_uuid(uuid)

    def list_courses(self) -> list[Course]:
        """Return all available courses"""
        return self.courses.courses

    def search_free_slots(
        self,
        course: Course | list[Course],
        date: date,
        n_slots_to_look_for: int = 4,
        start_time: time | None = None,
        stop_time: time | None = None,
    ) -> list[Slot]:
        """List all open tee times given the predicaments. Require login.

        Parameters
        ----------
        course: Course | list[Course]
            Either Course or list of Course -- a course object containing id etc.
        date: datetime.date
            date -- eg. 20250523
        n_slots_to_look_for: int
            Number of people that should fit in the tee time (default is 4)
        start_time: datetime.time
            Earliest time to accept tee off (default to None which accept all)
        stop_time: datetime.time
            Latest time to accept tee off (default to None which accept all)
        """
        if isinstance(course, Course):
            course = [course]
        return list(
            itertools.chain(
                *[
                    filter_eligible_slots(
                        self.fetch_slots(c, date),
                        n_slots_to_look_for,
                        start_time,
                        stop_time,
                    )
                    for c in course
                ]
            )
        )

    def book_teetime(self, slot: Slot, players: list[str]):
        """Book a tee time on the website 'https://mingolf.golf.se/Site/Booking' for golf players.

        The function performs several requests on the site:
        1. Navigates to the main 'Booking' page.
        2. Checks the available slots.
        3. Initialises the booking.
        4. If players are specified, adds the players to the booking.
        5. Finalises the booking (saves the booking on the site).

        Parameters
        __________
        slot: Slot
            an object that contains SlotID, SlotTime, CourseID, OrganizationalunitID.
        players: list[str]
            players (list[str]): A list of player names to be added to the booking.

        Returns
        _______
        (dict): The site's response to the final 'booking' request.

        ```
        {
        "BookingCode": "A..2K",
        "ErrorMessage": null,
        "HasErrors": false,
        "IsEdit": true,
        "NewPlayerCount": 1,
        "Players": [
            {
            "Articles": [
                {
                "ArticleID": "da84ab67...asdasddasd",
                "ArticleName": "Greenfee enligt 3-7-4",
                "CreditsAmount": null,
                "EngagementID": false,
                "IsPartialPay": false,
                "Paid": false,
                "PartialPaid": false,
                "PartialPaidAmount": 0,
                "PartialPrice": 0,
                "Price": 565,
                "PriceRuleName": null,
                "SellingOrganization": "....."
                }
            ],
            "ClubName": "...",
            "CountryCode": "SE",
            "DataIndex": 0,
            "FirstName": "...",
            "FullName": "...",
            "Gender": 1,
            "GolfID": "...",
            "HCP": "19,6",
            "HCPGroup": 4,
            "IsSelf": true,
            "IsNineHole": false,
            "LastName": "...",
            "PayArticle": true,
            "ParticipantID": null,
            "PreBooked": false,
            "PreBookingFee": null,
            "Price": 565,
            "SelectedArticle": {
                "ArticleID": "....",
                "ArticleName": "Greenfee enligt 3-7-4",
                "CreditsAmount": null,
                "EngagementID": false,
                "IsPartialPay": false,
                "Paid": false,
                "PartialPaid": false,
                "PartialPaidAmount": 0,
                "PartialPrice": 0,
                "Price": 565,
                "PriceRuleName": null,
                "SellingOrganization": "4....a302-0f7a38c93567"
            },
            "SelectedRentalArticles": null,
            "RentalArticles": null,
            "TotalPaid": 0,
            "Union": 1,
            "ShowAsGuest": false
            }
        ],
        "Slot": {
            "BookingInfo": {
            "AvailableRentalArticle": true,
            "BookedPlayers": [
                {
                "BookedRentalArticles": [],
                "ExactHcp": "9,6",
                "FName": "...",
                "ForeignIDNumber": "",
                "Gender": 1,
                "GolfID": "....",
                "HomeClubName": "...",
                "LName": "...",
                "Price": "565,00"
                }
            ],
            "BookingCode": "LX....2K",
            "CourseID": "4bfc39cf-b2d2-4a32-ba81-a8db53e59bb2",
            "CourseName": "18-hålsbanan ",
            "HasArticleBookings": false,
            "HasPaidFees": false,
            "HasPartialPaidFees": false,
            "IdentifyAllWeb": true,
            "IsArticlePaymentMandatory": false,
            "IsNineHoleBookingAvailable": false,
            "IsGroupBooking": false,
            "IsPaymentDefault": true,
            "IsPaymentMandatory": false,
            "MandatoryPaymentValue": 0,
            "MandatoryPaymentValueType": 0,
            "MaxBookingsPerSlot": 4,
            "NoOfPlayers": 1,
            "NumberOfFreeSlots": 3,
            "OrgUnitID": "4fb14a3a-.......-0f7a38c93567",
            "OrganizationalUnitName": "... Golfklubb",
            "PreBookingFee": false,
            "ReceiptInfo": {
                "Email": "",
                "Phone": "",
                "PostalAddress": "",
                "PostalCode": ""
            },
            "Time": "20250724T073000",
            "TotalPrice": "565,00",
            "WebPayment": true
            },
            "DeletedPlayerCount": 0,
            "ExistingPlayers": [],
            "LoginPlayerIsBooker": true,
            "SlotId": "7dfd03ec-......-6a8063675674",
            "SlotLock": {
            "SlotId": "7dfd03ec.....-6a8063675674",
            "Expires": "202507...."
            },
            "Status": 0
        }
        }
        ```
        """
        book_teetime_url = "https://mingolf.golf.se/Site/Booking"
        check_availability = (
            "https://mingolf.golf.se/handlers/booking/CheckAvailability"
        )
        init_booking = "https://mingolf.golf.se/handlers/booking/InitBooking"
        save_booking = "https://mingolf.golf.se/handlers/booking/SaveBooking"
        self.session.get(book_teetime_url)
        pdata = {"slotId": slot.SlotID}
        data = {
            "slotId": slot.SlotID,
            "slotTime": slot.SlotTime,
            "courseId": slot.CourseID,
            "clubId": slot.OrganizationalunitID,
            "bookingCode": "",
        }
        _ = self.session.post(check_availability, data=data)
        init_booking = self.session.post(init_booking, data=pdata).json()
        if players:
            for player in players:
                self.add_player(player)
        book_teetime = self.session.post(save_booking).json()
        return book_teetime

    def add_player(self, golf_id: str):
        add_player = "https://mingolf.golf.se/handlers/booking/AddPlayerToBooking"
        response = self.session.post(
            add_player, data={"golfId": golf_id, "countryCode": "SE"}
        )
        if response.status_code == 200:
            res_data = response.json()
            if res_data["HasErrors"]:
                raise Exception(res_data["ErrorMessage"])

    def cancel_booking(self, slot: Slot) -> CancelBooking:
        """
        Delete a booking slot using the slot.

        Parameters
        ----------
        slot: Slot
            The unique identifier for the booking slot to be deleted.
            Require 1) SlotID and 2) SlotTime

        Returns
        -------
        bool
            True if the booking was successfully deleted, False otherwise.
        """
        now = datetime.now()
        now_str = now.strftime("%Y%m%dT%H%M%S")
        one_year_later = now + relativedelta(years=1)
        one_year_later_str = one_year_later.strftime("%Y%m%dT%H%M%S")

        data = {"slotId": slot.SlotID}
        pdata = {
            "slotId": slot.SlotID,
            "handler": "Details",
            "itemTime": slot.SlotTime,
            "listType": "future",
            "maxExpand": "6",
            "filterPeriodFrom": now_str,
            "filterPeriodTo": one_year_later_str,
        }
        CALENDER_URL = "https://mingolf.golf.se/Site/Calendar/"
        DELETE_BOOKED_TIME = "https://mingolf.golf.se/handlers/Booking/DeleteBooking"
        self.session.headers["Referer"] = "https://mingolf.golf.se/"
        _ = self.session.get(CALENDER_URL, params=pdata).json()
        response = self.session.post(DELETE_BOOKED_TIME, data=data).json()
        return CancelBooking.model_validate(response)

    def get_my_teetimes(self) -> list[TeeSlot]: ...
