from fastapi import FastAPI, Query
from golfkompis.course import load_courses
from golfkompis.mingolf import MinGolf
from datetime import time, date
import uvicorn

app = FastAPI()

# Golf courses
AGESTA_COURSE_ID = "bc50ce1c-e439-4fa8-8de0-baf8817aa1dd"
BOTKYRKA_COURSE_ID = "4bfc39cf-b2d2-4a32-ba81-a8db53e59bb2"
TROXHAMMAR_COURSE_ID = "98369cac-d4bb-4671-931f-db10201ba1a5"


@app.get("/booking/find")
async def find(
    date: date = Query(..., example="2025-07-24"),
    start: time = Query(..., example="07:30"),
    stop: time = Query(..., example="12:00"),
    spots: int = Query(..., example=4, max=4),
    username: str = Query(..., example="900922-018", min_length=10, max_length=10),
    password: str = Query(..., example="****"),
    # extra_players: list[str] = Query(..., example=["890221-012"]),
    courses: list[str] = Query(..., example=["98369cac-d4bb-4671-931f-db10201ba1a5"]),
):
    """Get available golf tee times for the requested date and time.
       Between time start and stop. Number of people that want to play is spots.

    RETURNS
    _______
    ```
    [
        {
            "CourseID": "98369cac-d4bb-4671-931f-db10201ba1a5",
            "CourseName": "Arton 18-hål",
            "MaximumNumberOfSlotBookingsPerSlot": 4,
            "OrganizationalunitID": "13794bff-9231-4dd9-bea0-283076683c0e",
            "OrganizationalunitName": "Troxhammar Golfklubb",
            "SlotID": "60ba185c-2fa2-4527-9826-e685efc0c36f",
            "SlotTime": "20250721T090000",
            "Status": 0,
            "FlexColor": 0,
            "CreditValue": null,
            "BookingCode": null,
            "SlotReservations": null
        },
       {
            "CourseID": "98369cac-d4bb-4671-931f-db10201ba1a5",
            "CourseName": "Arton 18-hål",
            "MaximumNumberOfSlotBookingsPerSlot": 4,
            "OrganizationalunitID": "13794bff-9231-4dd9-bea0-283076683c0e",
            "OrganizationalunitName": "Troxhammar Golfklubb",
            "SlotID": "30e6c0ad-f2b1-4b0d-bb64-04181a1c70a9",
            "SlotTime": "20250721T115000",
            "Status": 0,
            "FlexColor": 0,
            "CreditValue": null,
            "BookingCode": null,
            "SlotReservations": null
        }
    ]
    ```
    """

    golf = MinGolf()
    courses_list = [golf.get_courses_by_uuid(uuid) for uuid in courses]
    golf.login(username, password)
    all_free_slots = golf.search_free_slots(courses_list, date, spots, start, stop)
    return all_free_slots


@app.get("/booking/book")
async def book(
    date: date = Query(..., example="2025-07-24"),
    start: time = Query(..., example="07:30"),
    stop: time = Query(..., example="12:00"),
    spots: int = Query(..., example=4, max=4),
    username: str = Query(..., example="900922-018", min_length=10, max_length=10),
    password: str = Query(..., example="****"),
    extra_players_id: list[str] = Query(default=[]),
    courses: list[str] = Query(..., example=["98369cac-d4bb-4671-931f-db10201ba1a5"]),
):
    """
    RETURNS
    _______
    ```
    ```
    """

    golf = MinGolf()
    courses_list = [golf.get_courses_by_uuid(uuid) for uuid in courses]
    golf.login(username, password)
    all_free_slots = golf.search_free_slots(courses_list, date, spots, start, stop)
    result = golf.book_teetime(all_free_slots[0], extra_players_id)
    return result


@app.get("/course/search")
async def search(
    course: str = Query(..., example="Botkyrka"),
):
    """
    RETURNS
    _______
    ```
    ```
    """

    golf = MinGolf()
    return golf.search_courses(course)


if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
