"""Course catalogue loader and in-memory search index."""

import contextlib
import os
import tempfile
from pathlib import Path

from pydantic import BaseModel

from golfkompis.domain import Course

_COURSES_PATH = Path(__file__).parent / "resources" / "courses.json"


class Courses(BaseModel):
    courses: list[Course]

    def save(self, path: Path = _COURSES_PATH) -> None:
        """Write catalogue to *path* atomically (write-then-rename)."""
        gc_json = self.model_dump_json()
        dir_ = path.parent
        fd, tmp_path = tempfile.mkstemp(dir=dir_, suffix=".tmp")
        try:
            with os.fdopen(fd, "w") as fh:
                fh.write(gc_json)
            os.replace(tmp_path, path)
        except Exception:
            with contextlib.suppress(OSError):
                os.unlink(tmp_path)
            raise

    def search(self, name: str, only_18: bool = False) -> list[Course]:
        """Case-insensitive substring search over ClubName."""
        results = [c for c in self.courses if name.lower() in c.ClubName.lower()]
        if only_18:
            return [c for c in results if not c.IsNineHoleCourse]
        return results

    def get_uuid(self, uuid: str) -> Course:
        for course in self.courses:
            if uuid.lower() == course.CourseID.lower():
                return course
        raise KeyError(f"no such course with {uuid=}")


def load_courses(path: Path = _COURSES_PATH) -> "Courses":
    return Courses.model_validate_json(path.read_text())
