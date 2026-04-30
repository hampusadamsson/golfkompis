# AGENTS.md

## Stack
- Python 3.13, managed with `uv`. Never use `pip` or `python` directly.
- FastAPI (HTTP API) + argparse (CLI). Entry: `src/golfkompis/__main__.py`.
- Type checker: `basedpyright` in `strict` mode — not mypy.
- Linter/formatter: `ruff`. Line length 88.

## Setup
```bash
uv sync
uv run pre-commit install
```

## Dev commands
```bash
uv run pytest -q               # run tests (exit 5 = no tests collected, OK)
uv run ruff check src/         # lint
uv run ruff format src/        # format (--check to verify only)
uv run basedpyright            # type check
```

CI runs lint → format-check → typecheck → pytest. All must pass before merging.

## Tests
- Test path: `src/tests/`. Run a single file: `uv run pytest src/tests/test_foo.py -q`.
- Exit code 5 (no tests collected) is treated as success in CI and pre-commit.

## Ruff lint ignores (intentional, don't fix)
- `N815` — camelCase field names match MinGolf API responses
- `N818` — domain exception names like `BookingNotFound`
- `B008` — FastAPI `Query()` in function defaults
- `E501` — long lines not broken

## Architecture
```
src/golfkompis/
├── __main__.py      CLI dispatch
├── cli.py           argparse subcommands
├── app.py           FastAPI routes
├── mingolf.py       MinGolf HTTP client
├── domain.py        Pydantic models (mirrors MinGolf API shapes)
├── smart_filters.py slot filtering (timezone, spots, time window)
├── course.py        bundled course catalogue index
├── endpoints.py     MinGolf URL constants
├── config.py        settings (env / .env / CLI flags)
├── logging.py       structlog config
└── resources/courses.json   bundled club catalogue (snapshot, may be stale)
```

## Mock mode
Set `MOCK=1` to avoid real MinGolf calls. Fixtures in `src/golfkompis/fixtures/` are validated against Pydantic models at startup — corrupted fixtures fail loudly.

## Releases
Conventional Commits on `main`. `fix:` = patch, `feat:` = minor, `feat!:` = major. `chore:`, `test:`, `ci:` don't appear in changelog. Release-please automates versioning.

## Credentials
`MINGOLF_USERNAME` (format `YYMMDD-XXX`) and `MINGOLF_PASSWORD` required for real calls. `.env` is gitignored. Precedence: CLI flag > env var > `.env`.
