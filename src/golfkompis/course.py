import os

from pydantic import BaseModel

from golfkompis.domain import Course

courses_path = os.path.join(os.path.dirname(__file__), "./resources/courses.json")


class Courses(BaseModel):
    courses: list[Course]

    def save(self):
        with open(courses_path, "w") as fn:
            gc_json = self.model_dump_json()
            _ = fn.write(str(gc_json))

    def search(self, name: str) -> list[Course]:
        return list(
            filter(
                lambda x: name.lower() in x.ClubName.lower() if x else "", self.courses
            )
        )

    def get_uuid(self, uuid: str) -> Course:
        for course in self.courses:
            if course and uuid.lower() == course.CourseID.lower():
                return course
        raise Exception(f"no such course with {uuid=}")


def load_courses() -> Courses:
    with open(courses_path) as fn:
        return Courses.model_validate_json(fn.read())
