# Backend — Golfkompis

Python 3.13 · FastAPI · fastapi-users · uv

For setup, configuration, Docker build, deploy, and email configuration see the [root README](../README.md).

---

## Quickstart (backend only)

```bash
cd backend
uv sync
cp ../.env.example ../.env   # edit MINGOLF_USERNAME and MINGOLF_PASSWORD
uv run uvicorn golfkompis.app:app --reload
```

Interactive API docs at http://localhost:8000/docs (Swagger) and `/redoc`.

---

## CLI

```bash
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

Use `golfkompis help <command>` or `golfkompis <command> --help` for details.

### find

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

Output is a JSON array of available slots. The `id` field is what `book` expects.

### book

> ⚠ **Destructive** — books the slot immediately.

```bash
uv run golfkompis book --slot-id <slot-id>
```

### cancel

> ⚠ **Destructive** — cancels the booking immediately.

```bash
uv run golfkompis cancel --booking-id <booking-id>
```

Booking IDs appear in the output of `bookings`.

### bookings

```bash
uv run golfkompis bookings
uv run golfkompis bookings --to 2026-06-01
```

### history

```bash
uv run golfkompis history
uv run golfkompis history --from 2025-01-01 --to 2025-12-31
```

### courses

```bash
uv run golfkompis courses --name Botkyrka
uv run golfkompis courses --name Botkyrka --eighteen-only
```

### profile / friends

```bash
uv run golfkompis profile
uv run golfkompis friends
```

---

## HTTP API

### Mock mode

Set `MOCK=1` to serve canned fixture data — no MinGolf credentials needed:

```bash
MOCK=1 uv run uvicorn golfkompis.app:app --reload
```

In mock mode all read endpoints return fixtures from `src/golfkompis/fixtures/`. Write endpoints (`POST /booking`, `DELETE /bookings/{id}`) always return `204`.

### Endpoints

| Method | Path | Auth | Summary |
|--------|------|------|---------|
| `GET` | `/health` | — | Liveness probe |
| `GET` | `/api/v1/booking/find` | ✓ | Search available tee times |
| `POST` | `/api/v1/booking` | ✓ | Book a tee slot |
| `GET` | `/api/v1/bookings` | ✓ | List upcoming bookings |
| `DELETE` | `/api/v1/bookings/{booking_id}` | ✓ | Cancel a booking |
| `GET` | `/api/v1/history` | ✓ | List played rounds |
| `GET` | `/api/v1/course/search` | — | Search course catalogue |
| `GET` | `/api/v1/course/list` | — | List all courses |
| `GET` | `/api/v1/profile` | ✓ | Fetch user profile |
| `GET` | `/api/v1/friends` | ✓ | Fetch friend overview |
| `POST` | `/auth/register` | — | Register a new account |
| `POST` | `/auth/login` | — | Log in (sets session cookie) |
| `POST` | `/auth/forgot-password` | — | Request password reset email |
| `POST` | `/auth/reset-password` | — | Confirm password reset |
| `POST` | `/auth/request-verify-token` | — | Resend verification email |
| `POST` | `/auth/verify` | — | Verify email with token |
| `GET` | `/users/me` | ✓ | Get current user |
| `PATCH` | `/users/me` | ✓ | Update profile |
| `PATCH` | `/users/me/mingolf` | ✓ | Store MinGolf credentials |
| `GET` | `/api/v1/queue` | ✓ | List queue entries |
| `POST` | `/api/v1/queue` | ✓ | Create a queue entry |
| `GET` | `/api/v1/queue/{id}` | ✓ | Get a queue entry |
| `PATCH` | `/api/v1/queue/{id}` | ✓ | Update a queue entry |
| `DELETE` | `/api/v1/queue/{id}` | ✓ | Cancel a queue entry |

Auth ✓ = requires a logged-in session cookie.

### Error codes

| Status | Meaning |
|--------|---------|
| `400` | Invalid request |
| `401` | Not authenticated |
| `404` | Resource not found |
| `409` | Conflict (slot taken, entry not active) |
| `412` | MinGolf credentials not linked |
| `422` | Validation error |
| `429` | MinGolf rate limit |
| `502` | MinGolf upstream error |

---

## Project layout

```
src/golfkompis/
├── __main__.py        CLI entrypoint
├── cli.py             argparse subcommands
├── app.py             FastAPI routes + SPA static serving
├── mingolf.py         MinGolf HTTP client
├── domain.py          Pydantic models (mirrors MinGolf API shapes)
├── smart_filters.py   Slot filtering (timezone, spots, time window)
├── course.py          Bundled course catalogue index
├── endpoints.py       MinGolf URL constants
├── config.py          Settings (env / .env)
├── logging.py         structlog config
├── users/             fastapi-users: models, manager, auth, email
├── queue/             Tee-time search queue: models, routes, worker
└── resources/
    └── courses.json   Bundled club/course catalogue snapshot
```

---

## Development

Install git hooks (one-time):

```bash
uv run pre-commit install
```

Run checks manually (same order as CI):

```bash
uv run ruff check src/
uv run ruff format --check src/
uv run basedpyright
uv run pytest src/tests/ -q
```
