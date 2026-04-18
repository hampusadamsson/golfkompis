# Golfkompis

![logo](logo.png)

Search for tee times at Swedish golf courses via MinGolf.

Features:

- Search tee slots across multiple courses simultaneously
- Filter by time window and number of available spots
- Times returned in Europe/Stockholm regardless of API timezone

## Requirements

- Python 3.12+
- [uv](https://github.com/astral-sh/uv)

## Install

```bash
uv sync
```

## CLI

```
uv run python src/cli.py
```

```
Tee time search tool for MinGolf Sweden.

USAGE
  golfkompis <command> [flags]

MAIN COMMANDS
  find      Find available tee times at one or more courses
  search    Search courses by club name
  courses   List all available courses
```

### find

Find available tee times for a given date, time window, and number of spots.

```bash
uv run python src/cli.py find \
  --username 900922-018 \
  --password '****' \
  --date 2026-04-21 \
  --start 08:00 \
  --stop 12:00 \
  --spots 4 \
  --courses 98369cac-d4bb-4671-931f-db10201ba1a5
```

Multiple courses can be passed:

```bash
  --courses 98369cac-d4bb-4671-931f-db10201ba1a5 4bfc39cf-b2d2-4a32-ba81-a8db53e59bb2
```

Output is a JSON array of available slots:

```json
[
  {
    "id": "c06813eb-2927-4e3a-8b51-700f4af7b492",
    "time": "2026-04-21T06:00:00",
    "price": { "greenfee": 450 },
    "flexColor": "None",
    "nineHoleBookingAavailable": false,
    "isLocked": false,
    "availablity": {
      "bookable": true,
      "maxNumberOfSlotBookings": 4,
      "numbersOfSlotBookings": 0,
      "numberOfBlockedRows": 0,
      "numberOfNineHoleSlotBookings": 0,
      "availableSlots": 4
    },
    "playersInfo": [],
    "reservationIds": [],
    "startProhibitionIds": [],
    "maximumHcpPerSlot": null
  }
]
```

### search

Search for courses by club name.

```bash
uv run python src/cli.py search --name Botkyrka
```

### courses

List all available courses.

```bash
uv run python src/cli.py courses
```

## MinGolf API reference

### Login

`POST https://mingolf.golf.se/login/api/Users/Login`

```json
{ "GolfId": "800222-027", "Password": "dummy123" }
```

### Course schedule

`GET https://mingolf.golf.se/bokning/api/Clubs/{clubId}/CourseSchedule`

Query params:

- `courseId` — course UUID
- `date` — `YYYY-MM-DD`

Response shape: `CourseSchedule` (see `src/golfkompis/domain2.py`).

Slot times are returned in UTC (`Z`). The CLI and filter layer convert them to `Europe/Stockholm` before applying any time window filter.
