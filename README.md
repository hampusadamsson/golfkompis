# Golfkompis

![logo](backend/logo.png)

[![CI Backend](https://github.com/hampusadamsson/golfkompis/actions/workflows/ci-backend.yml/badge.svg)](https://github.com/hampusadamsson/golfkompis/actions/workflows/ci-backend.yml)
[![CI Frontend](https://github.com/hampusadamsson/golfkompis/actions/workflows/ci-frontend.yml/badge.svg)](https://github.com/hampusadamsson/golfkompis/actions/workflows/ci-frontend.yml)
[![Release Please](https://github.com/hampusadamsson/golfkompis/actions/workflows/release-please.yml/badge.svg)](https://github.com/hampusadamsson/golfkompis/actions/workflows/release-please.yml)
[![Dependabot Updates](https://github.com/hampusadamsson/golfkompis/actions/workflows/dependabot/dependabot-updates/badge.svg)](https://github.com/hampusadamsson/golfkompis/actions/workflows/dependabot/dependabot-updates)

Unofficial web app for searching and booking tee times at Swedish golf courses via the MinGolf platform. Includes user accounts, per-user MinGolf credential storage, and a tee-time search queue that polls on a schedule and emails you when a matching slot opens.

## Repo layout

```
backend/    Python 3.13 · FastAPI · fastapi-users · uv
frontend/   SvelteKit 2 · Svelte 5 runes · Tailwind v4 · pnpm
Dockerfile  Multi-stage build: frontend → backend deps → runtime image
.github/    CI per-package · release-please monorepo config
```

---

## Quickstart (local dev)

You need: [uv](https://github.com/astral-sh/uv), [pnpm](https://pnpm.io/), Docker (for Mailpit).

**1. Copy env file and fill in your MinGolf credentials:**

```bash
cp .env.example .env
# edit MINGOLF_USERNAME and MINGOLF_PASSWORD
```

**2. Start the backend** (runs on http://localhost:8000):

```bash
cd backend
uv sync
uv run uvicorn golfkompis.app:app --reload
```

**3. Start the frontend dev server** (runs on http://localhost:5173):

```bash
cd frontend
pnpm install
pnpm dev
```

**4. Start Mailpit** to catch outgoing emails locally:

```bash
docker run -d --name mailpit -p 1025:1025 -p 8025:8025 axllent/mailpit
```

The default `.env` already points at Mailpit (`MAIL_SERVER=localhost`, `MAIL_PORT=1025`). Open http://localhost:8025 to inspect sent emails (verification, password reset, queue match notifications).

Open the app at **http://localhost:5173**.

---

## Configuration

All settings are read from environment variables (or a `.env` file in the repo root, which is gitignored). Copy `.env.example` to get started.

### MinGolf

| Variable            | Default | Description |
|---------------------|---------|-------------|
| `MINGOLF_USERNAME`  | —       | Golf-ID, format `YYMMDD-XXX`. Required for real MinGolf calls. |
| `MINGOLF_PASSWORD`  | —       | MinGolf password. |
| `MOCK`              | `false` | Set `1` to serve fixture data instead of calling MinGolf. |

> In the web app, per-user MinGolf credentials are stored in the user database (not in env vars). The env vars above are only used by the CLI or for a single-user server deployment.

### Auth / user management

| Variable                   | Default (dev)                       | Production value |
|----------------------------|-------------------------------------|------------------|
| `AUTH_SECRET`              | `changeme-replace-in-production`    | Random 32+ char string |
| `AUTH_DATABASE_URL`        | `sqlite+aiosqlite:///./users.db`    | Absolute path, e.g. `sqlite+aiosqlite:////data/users.db` |
| `AUTH_COOKIE_SECURE`       | `false`                             | `true` |
| `AUTH_FRONTEND_BASE_URL`   | `http://localhost:5173`             | `https://golfkompis.example.com` |

`AUTH_FRONTEND_BASE_URL` is the only URL you need to set — `/verify` and `/reset-password` paths are derived from it automatically.

### Email

| Variable        | Default (dev, Mailpit) | Production (smtp2go) |
|-----------------|------------------------|----------------------|
| `MAIL_FROM`     | `noreply@example.com`  | `noreply@yourdomain.tld` |
| `MAIL_SERVER`   | `localhost`            | `mail.smtp2go.com` |
| `MAIL_PORT`     | `1025`                 | `2525` |
| `MAIL_STARTTLS` | `false`                | `true` |
| `MAIL_SSL_TLS`  | `false`                | `false` |
| `MAIL_USERNAME` | _(empty)_              | smtp2go SMTP username |
| `MAIL_PASSWORD` | _(empty)_              | smtp2go API password |

### Queue

| Variable                       | Default | Description |
|--------------------------------|---------|-------------|
| `QUEUE_ENABLED`                | `true`  | Enable the background tee-time search worker. |
| `QUEUE_POLL_INTERVAL_MINUTES`  | `60`    | How often the worker checks active queue entries. |
| `QUEUE_ACTIVE_WINDOW_START`    | `08:00` | Earliest time of day the worker will run (Stockholm). |
| `QUEUE_ACTIVE_WINDOW_STOP`     | `23:00` | Latest time of day the worker will run (Stockholm). |
| `QUEUE_EMAIL_MAX_SLOTS`        | `20`    | Max number of matching slots included in the match email. |

---

## Email

### Dev — Mailpit

[Mailpit](https://github.com/axllent/mailpit) is a local SMTP catcher. All emails sent by the backend land in its web UI instead of going anywhere.

```bash
docker run -d --name mailpit -p 1025:1025 -p 8025:8025 axllent/mailpit
```

- SMTP on port 1025 (matches `MAIL_PORT=1025` default)
- Web UI at http://localhost:8025
- No credentials needed

To test the full flow: register a user at http://localhost:5173/register → check http://localhost:8025 → click the verification link.

### Production — smtp2go

Create an SMTP user in your [smtp2go account](https://app.smtp2go.com/) and verify your sender domain (SPF + DKIM). Then set these env vars in production:

```
MAIL_SERVER=mail.smtp2go.com
MAIL_PORT=2525
MAIL_STARTTLS=true
MAIL_SSL_TLS=false
MAIL_USERNAME=<your-smtp2go-username>
MAIL_PASSWORD=<your-smtp2go-api-password>
MAIL_FROM=noreply@yourdomain.tld
```

---

## Build (Docker)

Build from the **repo root** (both `backend/` and `frontend/` paths are needed):

```bash
docker build -t golfkompis:latest .
```

The build has three stages:

1. **frontend-builder** (`node:22-alpine`) — `pnpm install --frozen-lockfile` + `pnpm build`. Produces the static SvelteKit bundle.
2. **backend-builder** (`python:3.13-slim`) — `uv sync --frozen --no-dev`. Produces the Python venv.
3. **runtime** (`python:3.13-slim`) — copies venv + source from stage 2, copies frontend bundle from stage 1 into `/app/static`, runs as non-root user.

The backend auto-detects `/app/static` at startup and serves the SPA from there. API routes (`/api/v1/…`, `/auth/…`, `/health`) are served directly; everything else falls back to `index.html` for SvelteKit client-side routing.

Smoke test the image locally:

```bash
docker run --rm -p 8000:8000 --env-file .env golfkompis:latest
curl http://localhost:8000/health
# → {"status":"ok"}
```

---

## Deploy

### Push to a registry

```bash
docker tag golfkompis:latest ghcr.io/<owner>/golfkompis:latest
docker push ghcr.io/<owner>/golfkompis:latest
```

### Run on the host

```bash
docker run -d \
  --name golfkompis \
  --restart=unless-stopped \
  -p 8000:8000 \
  --env-file /etc/golfkompis.env \
  -v /var/lib/golfkompis:/data \
  ghcr.io/<owner>/golfkompis:latest
```

Mount a host directory to `/data` so the SQLite users database survives container restarts, and set `AUTH_DATABASE_URL=sqlite+aiosqlite:////data/users.db` in your env file.

### Production env checklist

These settings **must** differ from the dev defaults:

- `AUTH_SECRET` — random 32+ character string (`openssl rand -hex 32`)
- `AUTH_COOKIE_SECURE=true`
- `AUTH_FRONTEND_BASE_URL=https://golfkompis.example.com`
- `AUTH_DATABASE_URL=sqlite+aiosqlite:////data/users.db` (four slashes = absolute path)
- `MAIL_SERVER`, `MAIL_PORT`, `MAIL_STARTTLS`, `MAIL_USERNAME`, `MAIL_PASSWORD`, `MAIL_FROM` — see smtp2go section above

### TLS (reverse proxy)

The container speaks plain HTTP on port 8000. Terminate TLS with a reverse proxy. Minimal [Caddy](https://caddyserver.com/) config:

```
golfkompis.example.com {
    reverse_proxy localhost:8000
}
```

For nginx, proxy to `http://localhost:8000` and set `proxy_set_header X-Forwarded-Proto https;` — the backend respects forwarded headers (`--proxy-headers --forwarded-allow-ips=*`).

### Health check

The container has a built-in healthcheck that polls `http://localhost:8000/health` every 30 seconds. Your orchestrator can use this for rolling restarts. You can also check it manually:

```bash
docker inspect --format='{{.State.Health.Status}}' golfkompis
```

---

## Testing

### Backend

Run from `backend/`:

```bash
uv run ruff check src/          # lint
uv run ruff format --check src/ # format check
uv run basedpyright             # strict type check
uv run pytest src/tests/ -q     # tests (exit 5 = no tests = OK)
```

CI runs all four in order. Pre-commit hooks run the same checks on every commit (`uv run pre-commit install`).

### Frontend

Run from `frontend/`:

```bash
pnpm check   # svelte-check (type check)
pnpm lint    # prettier + eslint
pnpm test    # vitest
```

### Manual email flow test (dev)

1. Start Mailpit: `docker run -d -p 1025:1025 -p 8025:8025 axllent/mailpit`
2. Start backend: `cd backend && uv run uvicorn golfkompis.app:app --reload`
3. Register at http://localhost:5173/register
4. Open Mailpit at http://localhost:8025 — verification email should appear
5. Click the verification link — it redirects to `/verify?token=…` on the frontend
6. Test password reset from http://localhost:5173/forgot-password in the same way

---

## CI / Releases

GitHub Actions run separate pipelines for each package:

- **[ci-backend](.github/workflows/ci-backend.yml)** — triggers on `backend/**` changes: ruff lint + format check → basedpyright → pytest
- **[ci-frontend](.github/workflows/ci-frontend.yml)** — triggers on `frontend/**` changes: `pnpm check` + `pnpm lint` → `pnpm build`
- **[docker](.github/workflows/docker.yml)** — smoke-builds the Docker image on changes to either package or the Dockerfile (no push)
- **[release-please](.github/workflows/release-please.yml)** — auto-opens release PRs from Conventional Commits; tags as `backend-vX.Y.Z` and `frontend-vX.Y.Z` independently

Commit prefix guide:

| Prefix | Version bump |
|--------|-------------|
| `fix:` | patch |
| `feat:` | minor |
| `feat!:` / `BREAKING CHANGE:` | major |
| `chore:`, `test:`, `ci:` | no changelog entry |

---

## Disclaimer

Golfkompis is an **unofficial** client. It is not affiliated with, endorsed by, or supported by Svenska Golfförbundet, MinGolf, or any operator of the underlying API. The MinGolf API is undocumented and may change without notice. Use at your own risk.
