"""FastAPI app for golfkompis - tee time search."""

from datetime import date, time

import uvicorn
from fastapi import FastAPI, Query

from golfkompis.course import load_courses
from golfkompis.mingolf import MinGolf

app = FastAPI()

_courses = load_courses()


@app.get("/booking/find")
async def find(
    date: date = Query(..., example="2025-07-24"),
    start: time = Query(..., example="07:30"),
    stop: time = Query(..., example="12:00"),
    spots: int = Query(..., example=4),
    username: str = Query(..., example="900922-018", min_length=10, max_length=10),
    password: str = Query(..., example="****"),
    courses: list[str] = Query(..., example=["98369cac-d4bb-4671-931f-db10201ba1a5"]),
):
    """Get available golf tee times for the requested date and time window.

    Returns a list of available slots across the requested courses.
    """
    golf = MinGolf()
    golf.login(username, password)
    courses_list = [_courses.get_uuid(uuid) for uuid in courses]
    return golf.find_available_slots(courses_list, date, spots, start, stop)


@app.get("/course/search")
async def search(
    course: str = Query(..., example="Botkyrka"),
):
    """Search for courses by name."""
    return _courses.search(course)


if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
