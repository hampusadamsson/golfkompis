"""This is the cli version of the golfkompis app."""

import argparse
import json
import sys
from datetime import date, time

from golfkompis.course import load_courses
from golfkompis.mingolf import MinGolf

MAIN_COMMANDS = {
    "find": "Find available tee times at one or more courses",
    "search": "Search courses by club name",
    "courses": "List all available courses",
}

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


def cmd_search(args):
    courses = load_courses()
    results = courses.search(args.name)
    print(json.dumps([c.model_dump() for c in results], indent=2, ensure_ascii=False))


def cmd_courses(args):
    courses = load_courses()
    print(
        json.dumps(
            [c.model_dump() for c in courses.courses], indent=2, ensure_ascii=False
        )
    )


def cmd_find(args):
    courses = load_courses()
    courses_list = [courses.get_uuid(uuid) for uuid in args.courses]

    search_date = date.fromisoformat(args.date)
    start_time = time.fromisoformat(args.start) if args.start else None
    stop_time = time.fromisoformat(args.stop) if args.stop else None

    golf = MinGolf()
    golf.login(args.username, args.password)
    slots = golf.find_available_slots(
        courses_list,
        search_date,
        min_spots=args.spots,
        start_time=start_time,
        stop_time=stop_time,
    )
    print(json.dumps([s.model_dump() for s in slots], indent=2, ensure_ascii=False))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="golfkompis",
        add_help=False,  # we handle help manually
    )
    parser.add_argument(
        "-h", "--help", action="store_true", help="Show this help message."
    )
    sub = parser.add_subparsers(dest="command")

    # find
    p_find = sub.add_parser(
        "find",
        description="Find available tee times at one or more courses.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p_find.add_argument("--username", required=True, help="Golf-ID (YYMMDD-XXX).")
    p_find.add_argument("--password", required=True, help="MinGolf password.")
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

    # search
    p_search = sub.add_parser(
        "search",
        description="Search courses by club name.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p_search.add_argument(
        "--name", required=True, help="Club/course name to search for."
    )

    # courses
    sub.add_parser(
        "courses",
        description="List all available courses.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    # help
    p_help = sub.add_parser("help", description="Show help for a command.")
    p_help.add_argument("topic", nargs="?", help="Command to show help for.")

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
        if args.command == "search":
            cmd_search(args)
        elif args.command == "courses":
            cmd_courses(args)
        elif args.command == "find":
            cmd_find(args)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
