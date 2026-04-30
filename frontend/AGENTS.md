# AGENTS.md

## Stack

- SvelteKit 2 + Svelte 5 (runes mode **enforced** for all non-`node_modules` files)
- TypeScript, Tailwind CSS v4, shadcn-svelte (vega style, lucide icons)
- Drizzle ORM + better-sqlite3 (SQLite)
- Static adapter (`@sveltejs/adapter-static`) — no SSR
- mdsvex: `.svx` and `.md` files are valid Svelte components/routes
- Package manager: **pnpm**

## Environment

Requires `DATABASE_URL` in `.env` (e.g. `DATABASE_URL=local.db`). Copy `.env.example`.

## Key Commands

```sh
pnpm dev              # dev server
pnpm build            # production build
pnpm check            # svelte-kit sync + svelte-check (typecheck)
pnpm lint             # prettier check + eslint
pnpm format           # prettier write
pnpm test             # vitest --run (unit + component)
pnpm test:unit        # vitest (watch mode)

# DB (requires DATABASE_URL set)
pnpm db:push          # push schema to db (dev)
pnpm db:generate      # generate migration files
pnpm db:migrate       # run migrations
pnpm db:studio        # Drizzle Studio GUI
```

## Structure

```
src/
  lib/
    api/          # API client helpers
    auth/         # auth utilities
    components/   # shared Svelte components (ui/ = shadcn-svelte)
    hooks/        # Svelte hooks
    server/db/    # Drizzle client (index.ts) + schema (schema.ts)
    utils.ts      # cn() and other utils
  routes/         # SvelteKit file-based routes
    layout.css    # Tailwind base + shadcn CSS vars (referenced by components.json)
```

## Conventions

- **Svelte 5 runes only** — use `$state`, `$derived`, `$effect`, etc. No legacy `$:` or `export let` props without `$props()`.
- shadcn-svelte components live in `$lib/components/ui/`. Add new ones via `pnpm dlx shadcn-svelte@latest add <component>`.
- Tailwind CSS v4 — no `tailwind.config.js`; config is in CSS via `@theme`.
- DB schema changes: edit `src/lib/server/db/schema.ts`, then run `pnpm db:push` (dev) or `pnpm db:generate && pnpm db:migrate` (prod).
- Tests use `vitest-browser-svelte` with Playwright — component tests run in real browser context.

## Verification Order

`pnpm check` → `pnpm lint` → `pnpm test`
