from golfkompis.domain import Slot
from golfkompis.mingolf import MinGolf
from datetime import date


def test_course() -> None:
    golf = MinGolf()
    c = golf.search_courses("Ågesta")[0]
    # golf.login("900921-017", "088594")
    r = golf.fetch_slots(c, date.today())
    print(r)


def test_cancel_booking() -> None:
    golf = MinGolf()
    # golf.login("921-017", "594")
    golf.login("900921-017", "088594")
    reservation = Slot.model_construct(
        SlotID="cc5c75db-0fd7-49c6-a98a-c54370ef35eb", SlotTime="20250728T102000"
    )
    cb = golf.cancel_booking(reservation)
    assert cb.Deleted, cb.ErrorMessage


# def test_club() -> None:
#     # golf = MinGolf()
# golf.login("900921-017", "088594")
#
# alls = GolfCourses().list()
# for i, c in enumerate(alls):
#     print(i, "/", len(alls), c)
#     time.sleep(1)
#     gc = golf.get_clubinfo(c)
#     with open("data.json", "r") as fn:
#         clubs = Clubs.model_validate_json(fn.read())
#     clubs.add(gc)
#
#     with open("data.json", "w") as fn:
#         gc_json = clubs.model_dump_json()
#         fn.write(str(gc_json))
