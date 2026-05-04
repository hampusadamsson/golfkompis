# Frontend — Golfkompis

SvelteKit 2 · Svelte 5 runes · Tailwind v4 · pnpm

For setup, configuration, Docker build, deploy, and email see the [root README](../README.md).

---

## Dev commands

```bash
pnpm install      # install dependencies
pnpm dev          # dev server → http://localhost:5173
pnpm check        # svelte-check (type check)
pnpm lint         # prettier + eslint
pnpm format       # prettier write
pnpm test         # vitest
pnpm build        # production build (output: build/)
```

`DATABASE_URL` must be set (e.g. `DATABASE_URL=local.db`) — copy `../.env.example` to `../.env`.

See `AGENTS.md` in this directory for stack conventions, component patterns, and Drizzle DB commands.
