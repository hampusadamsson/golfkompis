# Golfkompis

![logo](logo.png)

[![Release Please](https://github.com/hampusadamsson/golfkompis/actions/workflows/release-please.yml/badge.svg)](https://github.com/hampusadamsson/golfkompis/actions/workflows/release-please.yml)
[![CI](https://github.com/hampusadamsson/golfkompis/actions/workflows/ci.yml/badge.svg)](https://github.com/hampusadamsson/golfkompis/actions/workflows/ci.yml)
[![Dependabot Updates](https://github.com/hampusadamsson/golfkompis/actions/workflows/dependabot/dependabot-updates/badge.svg)](https://github.com/hampusadamsson/golfkompis/actions/workflows/dependabot/dependabot-updates)

Unofficial Python SDK for MinGolf — search and book tee times at Swedish golf courses via CLI or HTTP API.

- Search tee slots across multiple courses simultaneously
- Filter by time window and number of available spots
- Times returned in Europe/Stockholm regardless of API timezone

## Quickstart

```bash
uv sync
cp .env.example .env   # edit with your MinGolf credentials
uv run golfkompis find --date 2026-05-01 --course Botkyrka
```

## Requirements

- Python 3.13
- [uv](https://github.com/astral-sh/uv)

## Install

```bash
uv sync
```

## Configuration

Credentials can be set as environment variables, in a `.env` file, or passed directly as CLI flags.

| Variable            | Required | Description                    |
| ------------------- | -------- | ------------------------------ |
| `MINGOLF_USERNAME`  | yes      | Golf-ID, format `YYMMDD-XXX`   |
| `MINGOLF_PASSWORD`  | yes      | MinGolf password               |

**Precedence:** CLI flag > environment variable > `.env`

Copy `.env.example` to `.env` and fill in your credentials — the `.env` file is gitignored.

## CLI

```bash
uv run golfkompis
```

```text
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

Use `golfkompis help <command>` or `golfkompis <command> --help` for details. Use `--version` to print the installed version.

### find

Find available tee times for a given date, optional time window, and minimum number of spots.

```bash
# By course UUID
uv run golfkompis find \
  --date 2026-04-21 \
  --start 08:00 \
  --stop 12:00 \
  --spots 4 \
  --courses 98369cac-d4bb-4671-931f-db10201ba1a5

# Multiple UUIDs
uv run golfkompis find --date 2026-04-21 \
  --courses 98369cac-d4bb-4671-931f-db10201ba1a5 4bfc39cf-b2d2-4a32-ba81-a8db53e59bb2

# By name substring (comma-separated, combinable with --courses)
uv run golfkompis find --date 2026-04-21 --course "Botkyrka,Haninge"
```

Output is a JSON array of available slots. The `id` field of each slot is what `book` expects.

### book

Book a slot by ID.

> ⚠ **Destructive** — books the slot immediately against your live MinGolf account. `--dry-run` is on the roadmap.

```bash
uv run golfkompis book --slot-id <slot-id>
```

### cancel

Cancel a booking by ID.

> ⚠ **Destructive** — cancels the booking immediately. `--dry-run` is on the roadmap.

```bash
uv run golfkompis cancel --booking-id <booking-id>
```

Booking IDs appear in the output of `bookings`.

### bookings

List upcoming bookings (defaults to the next 10 weeks):

```bash
uv run golfkompis bookings
uv run golfkompis bookings --to 2026-06-01
```

### history

List played rounds:

```bash
uv run golfkompis history
uv run golfkompis history --from 2025-01-01 --to 2025-12-31
```

Both flags default to today −10 weeks and today respectively.

### courses

Search courses by name:

```bash
uv run golfkompis courses --name Botkyrka
uv run golfkompis courses --name Botkyrka --eighteen-only
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

Run the development server:

```bash
uv run uvicorn golfkompis.app:app --reload
```

Interactive docs at `http://localhost:8000/docs` (Swagger) and `/redoc`. Liveness probe at `/health`.

### Auth

Pass credentials via headers on every request:

```
X-Mingolf-Username: YYMMDD-XXX
X-Mingolf-Password: yourpassword
```

> Credentials are validated against MinGolf on every request — no session is cached server-side. Avoid hammering the endpoint.

## Docker

```bash
docker build -t golfkompis .
docker run --rm -p 8000:8000 --env-file .env golfkompis
curl http://localhost:8000/health
```

The production image runs without `--reload`, as a non-root user, with a built-in healthcheck.

## Project layout

```text
src/golfkompis/
├── __main__.py        CLI entrypoint dispatch
├── cli.py             argparse subcommands
├── app.py             FastAPI HTTP layer
├── mingolf.py         MinGolf HTTP client
├── domain.py          Pydantic models for API payloads
├── smart_filters.py   Slot filtering (timezone, spots, time window)
├── course.py          Local courses.json index
├── endpoints.py       MinGolf URL constants
├── config.py          Settings (env + .env)
├── logging.py         structlog configuration
└── resources/
    └── courses.json   Bundled club/course catalogue
```

Endpoint URLs and response models live in `src/golfkompis/endpoints.py` and `src/golfkompis/domain.py`.

## Development

Install git hooks (one-time):

```bash
uv run pre-commit install
```

Hooks run ruff, basedpyright, and pytest on every commit. To run checks manually:

```bash
uv run pytest -q
uv run ruff check
uv run ruff format
uv run basedpyright
```

## Releases

Releases are automated via [release-please](https://github.com/googleapis/release-please). The version in `pyproject.toml` and `CHANGELOG.md` are kept in sync automatically.

**How it works:**

1. Merge commits to `main` following [Conventional Commits](https://www.conventionalcommits.org/).
2. Release-please opens a `chore: release X.Y.Z` PR containing the changelog and version bump.
3. Merging that PR creates the git tag (`vX.Y.Z`) and publishes a GitHub release.

**Commit message prefixes that trigger version bumps:**

| Prefix                                   | Version bump              |
| ---------------------------------------- | ------------------------- |
| `fix:`                                   | patch (`0.1.0` → `0.1.1`) |
| `feat:`                                  | minor (`0.1.0` → `0.2.0`) |
| `feat!:` or `BREAKING CHANGE:` in footer | major (`0.1.0` → `1.0.0`) |

Commits prefixed with `chore:`, `test:`, or `ci:` are not surfaced in the changelog.

## Disclaimer

Golfkompis is an **unofficial** client. It is not affiliated with, endorsed by, or supported by Svenska Golfförbundet, MinGolf, or any operator of the underlying API. The MinGolf API is undocumented and may change without notice. Use at your own risk — the author accepts no responsibility for misuse, rate-limiting, account suspension, or data loss.
