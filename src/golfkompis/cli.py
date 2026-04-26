"""This is the cli version of the golfkompis app."""

import argparse
import json
import sys
from datetime import date, time, timedelta

from golfkompis import smart_filters
from golfkompis.config import settings
from golfkompis.course import load_courses
from golfkompis.mingolf import MinGolf

MAIN_COMMANDS = {
    "find": "Find available tee times at one or more courses",
    "book": "Book a tee time by slot ID",
    "bookings": "List your upcoming bookings",
    "history": "List your played rounds",
    "cancel": "Cancel a booked tee time",
    "courses": "Search and list courses",
    "profile": "Fetch the logged-in user's MinGolf profile",
    "friends": "List your golfing friends",
}

DEFAULT_RANGE_WEEKS = 10

OTHER_COMMANDS = {
    "help": "Show help for a command",
}


def print_root_help():
    print("Tee time manager tool for Min Golf Sweden.")
    print()
    print("USAGE")
    print("  golfkompis <command> [flags]")
    print()
    print("MAIN COMMANDS")
    for cmd, desc in MAIN_COMMANDS.items():
        print(f"  {cmd:<10}{desc}")
    print()
    print("OTHER COMMANDS")
    for cmd, desc in OTHER_COMMANDS.items():
        print(f"  {cmd:<10}{desc}")
    print()
    print('Use "golfkompis <command> --help" for more information about a command.')


def _require_credentials(args: argparse.Namespace) -> tuple[str, str]:
    username: str | None = args.username or settings.mingolf_username  # pyright: ignore[reportAny]
    password: str | None = args.password or settings.mingolf_password  # pyright: ignore[reportAny]
    if not username or not password:
        print(
            "Error: credentials required via --username/--password, "
            "MINGOLF_USERNAME/MINGOLF_PASSWORD env vars, or .env file.",
            file=sys.stderr,
        )
        sys.exit(1)
    return username, password


def cmd_book(args: argparse.Namespace) -> None:
    username, password = _require_credentials(args)
    golf = MinGolf()
    golf.login(username, password)
    golf.book_teetime(args.slot_id)  # pyright: ignore[reportAny]
    print(f"Booked slot {args.slot_id}")  # pyright: ignore[reportAny]


def cmd_courses(args: argparse.Namespace) -> None:
    courses = load_courses()
    results = courses.search(args.name, args.eighteen_only)  # pyright: ignore[reportAny]
    print(json.dumps([c.model_dump() for c in results], indent=2, ensure_ascii=False))


def cmd_find(args: argparse.Namespace) -> None:
    courses = load_courses()
    courses_list = [courses.get_uuid(uuid) for uuid in args.courses]  # pyright: ignore[reportAny]

    search_date = date.fromisoformat(args.date)  # pyright: ignore[reportAny]
    start_time = time.fromisoformat(args.start) if args.start else None  # pyright: ignore[reportAny]
    stop_time = time.fromisoformat(args.stop) if args.stop else None  # pyright: ignore[reportAny]

    username, password = _require_credentials(args)

    golf = MinGolf()
    golf.login(username, password)
    schedule = golf.find_available_slots(
        courses_list,
        search_date,
    )
    slots = smart_filters.filter(schedule, start_time, stop_time, args.spots)  # pyright: ignore[reportAny]
    print(json.dumps([s.model_dump() for s in slots], indent=2, ensure_ascii=False))


def cmd_bookings(args: argparse.Namespace) -> None:
    from_date = date.today()
    to_date = (
        date.fromisoformat(args.to_date)  # pyright: ignore[reportAny]
        if args.to_date  # pyright: ignore[reportAny]
        else date.today() + timedelta(weeks=DEFAULT_RANGE_WEEKS)
    )
    username, password = _require_credentials(args)

    golf = MinGolf()
    golf.login(username, password)
    bookings = golf.fetch_bookings(from_date, to_date)
    print(json.dumps([b.model_dump() for b in bookings], indent=2, ensure_ascii=False))


def cmd_history(args: argparse.Namespace) -> None:
    from_date = (
        date.fromisoformat(args.from_date)  # pyright: ignore[reportAny]
        if args.from_date  # pyright: ignore[reportAny]
        else date.today() - timedelta(weeks=DEFAULT_RANGE_WEEKS)
    )
    to_date = date.fromisoformat(args.to_date) if args.to_date else date.today()  # pyright: ignore[reportAny]
    username, password = _require_credentials(args)

    golf = MinGolf()
    golf.login(username, password)
    calendar = golf.fetch_calendar(from_date, to_date)
    print(
        json.dumps(
            [b.model_dump() for b in calendar.playedRounds],
            indent=2,
            ensure_ascii=False,
        )
    )


def cmd_cancel(args: argparse.Namespace) -> None:
    username, password = _require_credentials(args)
    golf = MinGolf()
    golf.login(username, password)
    golf.cancel_booking(args.booking_id)  # pyright: ignore[reportAny]
    print(f"Cancelled booking {args.booking_id}")  # pyright: ignore[reportAny]


def cmd_profile(args: argparse.Namespace) -> None:
    username, password = _require_credentials(args)
    golf = MinGolf()
    golf.login(username, password)
    profile = golf.fetch_profile()
    print(json.dumps(profile.model_dump(), indent=2, ensure_ascii=False))


def cmd_friends(args: argparse.Namespace) -> None:
    username, password = _require_credentials(args)
    golf = MinGolf()
    golf.login(username, password)
    overview = golf.fetch_friends()
    print(json.dumps(overview.model_dump(), indent=2, ensure_ascii=False))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="golfkompis",
        add_help=False,  # we handle help manually
    )
    parser.add_argument(
        "-h", "--help", action="store_true", help="Show this help message."
    )
    sub = parser.add_subparsers(dest="command")

    # book
    p_book = sub.add_parser(
        "book",
        description="Book a tee time by slot ID.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p_book.add_argument(
        "--username",
        default=None,
        help="Golf-ID (YYMMDD-XXX). Overrides MINGOLF_USERNAME env var.",
    )
    p_book.add_argument(
        "--password",
        default=None,
        help="MinGolf password. Overrides MINGOLF_PASSWORD env var.",
    )
    p_book.add_argument(
        "--slot-id",
        dest="slot_id",
        required=True,
        help="Slot UUID to book (Slot.id from `golfkompis find`).",
    )

    # find
    p_find = sub.add_parser(
        "find",
        description="Find available tee times at one or more courses.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p_find.add_argument(
        "--username",
        default=None,
        help="Golf-ID (YYMMDD-XXX). Overrides MINGOLF_USERNAME env var.",
    )
    p_find.add_argument(
        "--password",
        default=None,
        help="MinGolf password. Overrides MINGOLF_PASSWORD env var.",
    )
    p_find.add_argument("--date", required=True, help="Date to search (YYYY-MM-DD).")
    p_find.add_argument("--start", default=None, help="Earliest tee time (HH:MM).")
    p_find.add_argument("--stop", default=None, help="Latest tee time (HH:MM).")
    p_find.add_argument(
        "--spots", type=int, default=4, help="Number of spots needed (default 4)."
    )
    p_find.add_argument(
        "--courses",
        required=True,
        nargs="+",
        metavar="UUID",
        help="One or more course UUIDs.",
    )

    # search courses
    p_courses = sub.add_parser(
        "courses",
        description="Search courses by club name.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p_courses.add_argument("--name", default="", help="Club/course name to search for.")
    p_courses.add_argument(
        "--eighteen-only",
        dest="eighteen_only",
        required=False,
        action="store_true",
        help="Only display 18-hole courses.",
    )

    # help
    p_help = sub.add_parser("help", description="Show help for a command.")
    p_help.add_argument("topic", nargs="?", help="Command to show help for.")

    # bookings
    p_bookings = sub.add_parser(
        "bookings",
        description="List your upcoming bookings.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p_bookings.add_argument(
        "--username",
        default=None,
        help="Golf-ID (YYMMDD-XXX). Overrides MINGOLF_USERNAME env var.",
    )
    p_bookings.add_argument(
        "--password",
        default=None,
        help="MinGolf password. Overrides MINGOLF_PASSWORD env var.",
    )
    p_bookings.add_argument(
        "--to",
        dest="to_date",
        default=None,
        help="End of date range (YYYY-MM-DD). Defaults to today + 10 weeks.",
    )

    # history
    p_history = sub.add_parser(
        "history",
        description="List your played rounds.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p_history.add_argument(
        "--username",
        default=None,
        help="Golf-ID (YYMMDD-XXX). Overrides MINGOLF_USERNAME env var.",
    )
    p_history.add_argument(
        "--password",
        default=None,
        help="MinGolf password. Overrides MINGOLF_PASSWORD env var.",
    )
    p_history.add_argument(
        "--from",
        dest="from_date",
        default=None,
        help="Start of date range (YYYY-MM-DD). Defaults to today - 10 weeks.",
    )
    p_history.add_argument(
        "--to",
        dest="to_date",
        default=None,
        help="End of date range (YYYY-MM-DD). Defaults to today.",
    )

    # cancel
    p_cancel = sub.add_parser(
        "cancel",
        description="Cancel a booked tee time by booking id.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p_cancel.add_argument(
        "--username",
        default=None,
        help="Golf-ID (YYMMDD-XXX). Overrides MINGOLF_USERNAME env var.",
    )
    p_cancel.add_argument(
        "--password",
        default=None,
        help="MinGolf password. Overrides MINGOLF_PASSWORD env var.",
    )
    p_cancel.add_argument(
        "--booking-id",
        dest="booking_id",
        required=True,
        help="Booking UUID to cancel (bookingInfo.bookingId from `golfkompis bookings`).",
    )

    # profile
    p_profile = sub.add_parser(
        "profile",
        description="Fetch the logged-in user's MinGolf profile.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p_profile.add_argument(
        "--username",
        default=None,
        help="Golf-ID (YYMMDD-XXX). Overrides MINGOLF_USERNAME env var.",
    )
    p_profile.add_argument(
        "--password",
        default=None,
        help="MinGolf password. Overrides MINGOLF_PASSWORD env var.",
    )

    # friends
    p_friends = sub.add_parser(
        "friends",
        description="List your golfing friends.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p_friends.add_argument(
        "--username",
        default=None,
        help="Golf-ID (YYMMDD-XXX). Overrides MINGOLF_USERNAME env var.",
    )
    p_friends.add_argument(
        "--password",
        default=None,
        help="MinGolf password. Overrides MINGOLF_PASSWORD env var.",
    )

    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()

    # no command or explicit --help → print root help
    if not args.command or args.help:
        print_root_help()
        sys.exit(0)

    if args.command == "help":
        topic = getattr(args, "topic", None)
        if topic:
            parser.parse_args([topic, "--help"])
        else:
            print_root_help()
        sys.exit(0)

    try:
        if args.command == "courses":
            cmd_courses(args)
        elif args.command == "find":
            cmd_find(args)
        elif args.command == "book":
            cmd_book(args)
        elif args.command == "bookings":
            cmd_bookings(args)
        elif args.command == "history":
            cmd_history(args)
        elif args.command == "cancel":
            cmd_cancel(args)
        elif args.command == "profile":
            cmd_profile(args)
        elif args.command == "friends":
            cmd_friends(args)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
