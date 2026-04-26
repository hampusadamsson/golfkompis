# Golfkompis

![logo](logo.png)

Search for tee times at Swedish golf courses via MinGolf.

Features:

- Search tee slots across multiple courses simultaneously
- Filter by time window and number of available spots
- Times returned in Europe/Stockholm regardless of API timezone

## Requirements

- Python 3.13
- [uv](https://github.com/astral-sh/uv)

## Install

```bash
uv sync
```

## Development

Install git hooks (one-time):

```bash
uv run pre-commit install
```

Hooks run ruff, basedpyright, and pytest on every commit.

## CLI

```
uv run golfkompis
```

```
Tee time manager tool for Min Golf Sweden.

USAGE
  golfkompis <command> [flags]

MAIN COMMANDS
  find        Find available tee times at one or more courses
  book        Book a tee time by slot ID
  bookings    List your upcoming bookings
  history     List your played rounds
  cancel      Cancel a booked tee time
  courses     Search and list courses
  profile     Fetch the logged-in user's MinGolf profile
  friends     List your golfing friends
```

Use `golfkompis <command> --help` for details on each command.

### Credentials

Credentials can be provided via flags, environment variables, or `.env`:

```bash
export MINGOLF_USERNAME=YYMMDD-XXX
export MINGOLF_PASSWORD=yourpassword
```

Or pass inline:

```bash
uv run golfkompis find --username YYMMDD-XXX --password yourpassword ...
```

### find

Find available tee times for a given date, time window, and number of spots.

```bash
uv run golfkompis find \
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

Or search by name:

```bash
  --course Botkyrka
```

Output is a JSON array of available slots.

### book

Book a slot by ID:

```bash
uv run golfkompis book --slot-id <slot-id>
```

### bookings

List upcoming bookings:

```bash
uv run golfkompis bookings
```

### cancel

Cancel a booking by ID:

```bash
uv run golfkompis cancel --booking-id <booking-id>
```

### history

List played rounds:

```bash
uv run golfkompis history --from 2025-01-01 --to 2025-12-31
```

### courses

Search courses by name:

```bash
uv run golfkompis courses --name Botkyrka
```

### profile

Fetch your MinGolf profile:

```bash
uv run golfkompis profile
```

### friends

List your golfing friends:

```bash
uv run golfkompis friends
```

## HTTP API

The FastAPI server exposes the same functionality over HTTP:

```bash
uv run uvicorn golfkompis.app:app --reload
```

Pass credentials via headers on every request:

```
X-Mingolf-Username: YYMMDD-XXX
X-Mingolf-Password: yourpassword
```

Interactive docs at `http://localhost:8000/docs`.

## Docker

```bash
docker build -t golfkompis .
docker run -p 8000:8000 golfkompis
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

Slot times are returned in UTC (`Z`). The CLI and filter layer convert them to `Europe/Stockholm` before applying any time window filter.

## Releases

Releases are automated via [release-please](https://github.com/googleapis/release-please). The version in `pyproject.toml` and `CHANGELOG.md` are kept in sync automatically.

**How it works:**

1. Merge commits to `main` following [Conventional Commits](https://www.conventionalcommits.org/).
2. Release-please opens a `chore: release X.Y.Z` PR containing the changelog and version bump.
3. Merging that PR creates the git tag (`vX.Y.Z`) and publishes a GitHub release.

**Commit message prefixes that trigger version bumps:**

| Prefix | Version bump |
|---|---|
| `fix:` | patch (`0.1.0` → `0.1.1`) |
| `feat:` | minor (`0.1.0` → `0.2.0`) |
| `feat!:` or `BREAKING CHANGE:` in footer | major (`0.1.0` → `1.0.0`) |

Commits prefixed with `chore:`, `test:`, or `ci:` are not surfaced in the changelog.

# NOTE Important!

I take no responsibility in how you use this software.
Any use is at your own risk.
