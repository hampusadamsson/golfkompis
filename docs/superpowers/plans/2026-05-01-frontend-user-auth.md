# Frontend User Authentication Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a parallel app-account auth system (register/login/forgot-password/verify/profile) to the SvelteKit frontend, connecting to the fastapi-users backend already deployed.

**Architecture:** A new `currentUser` runes store mirrors the existing `credentials` store for MinGolf. The API client gains a `users` endpoint module using `credentials: 'include'` for cookie-based auth. New static routes (`/login`, `/register`, `/forgot-password`, `/reset-password`, `/verify`, `/profile/account`) use hand-rolled runes forms following the existing `CredentialsForm` pattern. The Navbar shows the logged-in app-user name.

**Tech Stack:** SvelteKit 2, Svelte 5 runes, TypeScript, shadcn-svelte, Tailwind v4, vitest-browser-svelte, Playwright

---

## File Map

| Action | Path | Purpose |
|--------|------|---------|
| Create | `src/lib/api/endpoints/users.ts` | App-user API calls (register, login, logout, me, patch, delete, forgot-password, reset-password, request-verify, verify) |
| Modify | `src/lib/api/client.ts` | Add `UsersClient` type + spread `users(req)` into factory; add `cookieAuth` flag to `ApiConfig` |
| Create | `src/lib/auth/currentUser.svelte.ts` | `CurrentUserStore` runes class (parallel to `CredentialsStore`) |
| Modify | `src/routes/+layout.svelte` | Add boot-time `/users/me` check in `$effect` |
| Modify | `src/lib/components/Navbar.svelte` | Add app-user section alongside MinGolf section |
| Modify | `frontend/vite.config.ts` | Add `/auth/*` and `/users/*` proxy entries |
| Create | `src/routes/login/+page.svelte` | Login form |
| Create | `src/routes/register/+page.svelte` | Register form |
| Create | `src/routes/forgot-password/+page.svelte` | Forgot-password form |
| Create | `src/routes/reset-password/+page.svelte` | Reset-password form (reads `token` from URL) |
| Create | `src/routes/verify/+page.svelte` | Email verification (reads `token` from URL, auto-submits) |
| Create | `src/routes/profile/account/+page.svelte` | Account settings page |
| Create | `src/lib/auth/currentUser.svelte.test.ts` | Unit test for store |
| Create | `src/routes/login/login.svelte.test.ts` | Component test for login page |
| Create | `src/tests/auth.spec.ts` | Playwright e2e happy path |

---

## Task 1: Add `/auth/*` and `/users/*` Vite proxy entries

**Files:**
- Modify: `frontend/vite.config.ts`

- [ ] **Step 1: Add proxy entries**

```ts
// frontend/vite.config.ts — server.proxy section
proxy: {
    '/health': 'http://localhost:8000',
    '/api': 'http://localhost:8000',
    '/auth': 'http://localhost:8000',
    '/users': 'http://localhost:8000'
}
```

- [ ] **Step 2: Verify dev server starts**

```sh
cd frontend && pnpm check
```
Expected: 0 errors.

- [ ] **Step 3: Commit**

```sh
git add frontend/vite.config.ts
git commit -m "feat: proxy /auth and /users to backend in dev"
```

---

## Task 2: Users API endpoint module

**Files:**
- Create: `frontend/src/lib/api/endpoints/users.ts`
- Modify: `frontend/src/lib/api/client.ts`

- [ ] **Step 1: Write failing test**

Create `frontend/src/lib/api/endpoints/users.test.ts`:

```ts
import { describe, it, expect, vi } from 'vitest';
import { users } from './users.js';

describe('users endpoint', () => {
    it('register calls POST /auth/register', async () => {
        const req = vi.fn().mockResolvedValue({ id: '123', email: 'a@b.com', is_active: true, is_superuser: false, is_verified: false, username: null, full_name: null, age: null });
        const client = users(req);
        await client.register({ email: 'a@b.com', password: 'pw', username: null, full_name: null, age: null });
        expect(req).toHaveBeenCalledWith('POST', '/auth/register', expect.objectContaining({ body: expect.objectContaining({ email: 'a@b.com' }) }));
    });

    it('getMe calls GET /users/me', async () => {
        const req = vi.fn().mockResolvedValue({ id: '123', email: 'a@b.com', is_active: true, is_superuser: false, is_verified: false, username: null, full_name: null, age: null });
        const client = users(req);
        await client.getMe();
        expect(req).toHaveBeenCalledWith('GET', '/users/me', expect.anything());
    });
});
```

- [ ] **Step 2: Run test to verify it fails**

```sh
cd frontend && pnpm test --run --reporter=verbose src/lib/api/endpoints/users.test.ts
```
Expected: FAIL — "cannot find module './users.js'"

- [ ] **Step 3: Create `src/lib/api/endpoints/users.ts`**

```ts
import type { Requester } from '../client.js';

export interface AppUser {
    id: string;
    email: string;
    is_active: boolean;
    is_superuser: boolean;
    is_verified: boolean;
    username: string | null;
    full_name: string | null;
    age: number | null;
}

export interface UserCreate {
    email: string;
    password: string;
    username: string | null;
    full_name: string | null;
    age: number | null;
}

export interface UserUpdate {
    username?: string | null;
    full_name?: string | null;
    age?: number | null;
}

export function users(req: Requester) {
    return {
        /** Register a new user. Returns the created AppUser. */
        register(body: UserCreate): Promise<AppUser> {
            return req('POST', '/auth/register', { body });
        },
        /** Log in with email+password. Sets auth cookie. Returns 204. */
        login(body: { username: string; password: string }): Promise<void> {
            return req('POST', '/auth/login', { body });
        },
        /** Log out. Clears auth cookie. Returns 204. */
        logout(): Promise<void> {
            return req('POST', '/auth/logout', {});
        },
        /** Get the current authenticated user. */
        getMe(): Promise<AppUser> {
            return req('GET', '/users/me', {});
        },
        /** Update the current user's profile fields. */
        patchMe(body: UserUpdate): Promise<AppUser> {
            return req('PATCH', '/users/me', { body });
        },
        /** Delete the current user account. */
        deleteMe(): Promise<void> {
            return req('DELETE', '/users/me', {});
        },
        /** Request a password reset email. Returns 202. */
        forgotPassword(body: { email: string }): Promise<void> {
            return req('POST', '/auth/forgot-password', { body });
        },
        /** Submit a new password with the reset token. Returns 200. */
        resetPassword(body: { token: string; password: string }): Promise<void> {
            return req('POST', '/auth/reset-password', { body });
        },
        /** Request a new verification email. Returns 202. */
        requestVerify(body: { email: string }): Promise<void> {
            return req('POST', '/auth/request-verify-token', { body });
        },
        /** Verify email with token from link. Returns updated AppUser. */
        verifyEmail(body: { token: string }): Promise<AppUser> {
            return req('POST', '/auth/verify', { body });
        }
    };
}
```

- [ ] **Step 4: Run test to verify it passes**

```sh
cd frontend && pnpm test --run src/lib/api/endpoints/users.test.ts
```
Expected: PASS

- [ ] **Step 5: Wire into `client.ts`**

In `frontend/src/lib/api/client.ts`, add imports and extend the factory.

Add after the `friends` import:
```ts
import { users } from './endpoints/users.js';
import type { AppUser } from './endpoints/users.js';
```

Add to the `ApiConfig` interface a new optional flag:
```ts
/** If true, all requests include `credentials: 'include'` for cookie auth. */
cookieAuth?: boolean;
```

In `createRequester`, update the fetch call to include credentials when needed:
```ts
res = await config.fetch(url, {
    method,
    headers,
    body: body !== undefined ? JSON.stringify(body) : undefined,
    signal,
    credentials: config.cookieAuth ? 'include' : 'same-origin'
});
```

Add `UsersClient` type and spread into factory:
```ts
// near the other ReturnType declarations
type UsersClient = ReturnType<typeof users>;

// update ApiClient union
export type ApiClient = MetaClient &
    CoursesClient &
    BookingsClient &
    HistoryClient &
    ProfileClient &
    FriendsClient &
    UsersClient;
```

In `createRequester`:
```ts
const resolved: Required<ApiConfig> = {
    baseUrl: config.baseUrl ?? '',
    credentials: config.credentials ?? { username: '', password: '' },
    fetch: config.fetch ?? globalThis.fetch,
    cookieAuth: config.cookieAuth ?? false
};
```

In the factory return:
```ts
return {
    ...meta(req),
    ...courses(req),
    ...bookings(req),
    ...history(req),
    ...profile(req),
    ...friends(req),
    ...users(req)
};
```

- [ ] **Step 6: Verify types**

```sh
cd frontend && pnpm check
```
Expected: 0 errors.

- [ ] **Step 7: Commit**

```sh
git add frontend/src/lib/api/endpoints/users.ts frontend/src/lib/api/endpoints/users.test.ts frontend/src/lib/api/client.ts
git commit -m "feat: add users API endpoint module + cookieAuth flag"
```

---

## Task 3: `currentUser` runes store

**Files:**
- Create: `frontend/src/lib/auth/currentUser.svelte.ts`
- Create: `frontend/src/lib/auth/currentUser.svelte.test.ts`

- [ ] **Step 1: Write failing test**

Create `frontend/src/lib/auth/currentUser.svelte.test.ts`:

```ts
import { describe, it, expect } from 'vitest';
import { CurrentUserStore } from './currentUser.svelte.js';

describe('CurrentUserStore', () => {
    it('starts with null user and false loading', () => {
        const store = new CurrentUserStore();
        expect(store.user).toBeNull();
        expect(store.loading).toBe(false);
    });

    it('set() updates user', () => {
        const store = new CurrentUserStore();
        const user = { id: '1', email: 'a@b.com', is_active: true, is_superuser: false, is_verified: true, username: 'alice', full_name: 'Alice', age: 30 };
        store.set(user);
        expect(store.user).toEqual(user);
        expect(store.isLoggedIn).toBe(true);
    });

    it('clear() resets user', () => {
        const store = new CurrentUserStore();
        store.set({ id: '1', email: 'a@b.com', is_active: true, is_superuser: false, is_verified: true, username: null, full_name: null, age: null });
        store.clear();
        expect(store.user).toBeNull();
        expect(store.isLoggedIn).toBe(false);
    });
});
```

- [ ] **Step 2: Run test to verify it fails**

```sh
cd frontend && pnpm test --run src/lib/auth/currentUser.svelte.test.ts
```
Expected: FAIL — "cannot find module"

- [ ] **Step 3: Create the store**

Create `frontend/src/lib/auth/currentUser.svelte.ts`:

```ts
import type { AppUser } from '$lib/api/endpoints/users.js';

export class CurrentUserStore {
    user = $state<AppUser | null>(null);
    loading = $state(false);

    get isLoggedIn(): boolean {
        return this.user !== null;
    }

    set(user: AppUser): void {
        this.user = user;
    }

    clear(): void {
        this.user = null;
    }
}

export const currentUser = new CurrentUserStore();
```

- [ ] **Step 4: Run test to verify it passes**

```sh
cd frontend && pnpm test --run src/lib/auth/currentUser.svelte.test.ts
```
Expected: PASS

- [ ] **Step 5: Commit**

```sh
git add frontend/src/lib/auth/currentUser.svelte.ts frontend/src/lib/auth/currentUser.svelte.test.ts
git commit -m "feat: add currentUser runes store for app auth"
```

---

## Task 4: Boot-time session check in root layout

**Files:**
- Modify: `frontend/src/routes/+layout.svelte`

- [ ] **Step 1: Update `+layout.svelte`**

```svelte
<script lang="ts">
    import './layout.css';
    import favicon from '$lib/assets/favicon.svg';
    import Navbar from '$lib/components/Navbar.svelte';
    import { createApiClient } from '$lib/api';
    import { currentUser } from '$lib/auth/currentUser.svelte';

    let { children } = $props();

    $effect(() => {
        const api = createApiClient({ cookieAuth: true });
        api.getMe()
            .then((user) => currentUser.set(user))
            .catch(() => {
                // not logged in — leave currentUser.user as null
            });
    });
</script>

<svelte:head>
    <link rel="icon" href={favicon} />
    <title>Golfkompis</title>
</svelte:head>

<Navbar />
{@render children()}
```

- [ ] **Step 2: Verify types**

```sh
cd frontend && pnpm check
```
Expected: 0 errors.

- [ ] **Step 3: Commit**

```sh
git add frontend/src/routes/+layout.svelte
git commit -m "feat: check /users/me on boot to restore app session"
```

---

## Task 5: Update Navbar with app-user section

**Files:**
- Modify: `frontend/src/lib/components/Navbar.svelte`

The new Navbar shows:
1. Existing MinGolf auth area (unchanged — right side)
2. A new "Konto" link in the nav that shows `/profile/account` when logged in, else links to `/login`

Replace the `<nav>` section and auth area with:

- [ ] **Step 1: Update Navbar**

```svelte
<script lang="ts">
    import { page } from '$app/state';
    import { Button } from '$lib/components/ui/button';
    import {
        Dialog,
        DialogContent,
        DialogHeader,
        DialogTitle,
        DialogTrigger
    } from '$lib/components/ui/dialog';
    import CredentialsForm from './CredentialsForm.svelte';
    import { credentials } from '$lib/auth/credentials.svelte';
    import { currentUser } from '$lib/auth/currentUser.svelte';
    import { createApiClient } from '$lib/api';

    let loginOpen = $state(false);

    function handleSignIn() {
        loginOpen = false;
    }

    async function handleAppLogout() {
        const api = createApiClient({ cookieAuth: true });
        try {
            await api.logout();
        } finally {
            currentUser.clear();
        }
    }
</script>

<header class="border-b bg-background sticky top-0 z-40">
    <div class="mx-auto flex h-14 max-w-5xl items-center gap-6 px-4">
        <!-- Brand -->
        <!-- eslint-disable-next-line svelte/no-navigation-without-resolve -->
        <a href="/" class="text-lg font-bold tracking-tight">Golfkompis</a>

        <!-- Nav links -->
        <!-- eslint-disable svelte/no-navigation-without-resolve -->
        <nav class="flex items-center gap-4 text-sm">
            <a
                href="/"
                class={page.url.pathname === '/'
                    ? 'text-foreground font-medium'
                    : 'text-muted-foreground hover:text-foreground transition-colors'}
            >
                Hem
            </a>
            <a
                href="/profile"
                class={page.url.pathname === '/profile'
                    ? 'text-foreground whitespace-nowrap font-medium'
                    : 'text-muted-foreground hover:text-foreground whitespace-nowrap transition-colors'}
            >
                Min sida
            </a>
            <a
                href="/book"
                class={page.url.pathname === '/book'
                    ? 'text-foreground font-medium'
                    : 'text-muted-foreground hover:text-foreground transition-colors'}
            >
                Boka
            </a>
            <a
                href={currentUser.isLoggedIn ? '/profile/account' : '/login'}
                class={page.url.pathname.startsWith('/profile/account') || page.url.pathname === '/login'
                    ? 'text-foreground font-medium'
                    : 'text-muted-foreground hover:text-foreground transition-colors'}
            >
                Konto
            </a>
        </nav>
        <!-- eslint-enable svelte/no-navigation-without-resolve -->

        <div class="flex-1"></div>

        <!-- App auth area -->
        {#if currentUser.isLoggedIn}
            <span class="text-muted-foreground hidden text-sm sm:inline">
                {currentUser.user?.username ?? currentUser.user?.email}
            </span>
            <Button variant="ghost" size="sm" onclick={handleAppLogout}>Logga ut konto</Button>
        {:else}
            <!-- eslint-disable-next-line svelte/no-navigation-without-resolve -->
            <a href="/login">
                <Button variant="ghost" size="sm">Logga in konto</Button>
            </a>
        {/if}

        <!-- MinGolf auth area -->
        {#if credentials.profile}
            <span class="text-muted-foreground hidden text-sm sm:inline">
                {credentials.profile.firstName}
                {credentials.profile.lastName} · HCP {credentials.profile.hcp}
            </span>
            <Button variant="outline" size="sm" onclick={() => credentials.clear()}>MinGolf ut</Button>
        {:else}
            <Dialog bind:open={loginOpen}>
                <DialogTrigger>
                    {#snippet child({ props })}
                        <Button size="sm" {...props}>MinGolf in</Button>
                    {/snippet}
                </DialogTrigger>
                <DialogContent class="sm:max-w-md">
                    <DialogHeader>
                        <DialogTitle>Logga in på MinGolf</DialogTitle>
                    </DialogHeader>
                    <CredentialsForm onSubmit={handleSignIn} />
                </DialogContent>
            </Dialog>
        {/if}
    </div>
</header>
```

- [ ] **Step 2: Verify types**

```sh
cd frontend && pnpm check
```
Expected: 0 errors.

- [ ] **Step 3: Commit**

```sh
git add frontend/src/lib/components/Navbar.svelte
git commit -m "feat: surface app account in Navbar alongside MinGolf"
```

---

## Task 6: Login page (`/login`)

**Files:**
- Create: `frontend/src/routes/login/+page.svelte`

Pattern: match `CredentialsForm.svelte` exactly — `$state` for fields, `*Touched` flags, `$derived` for validation, inline `<Alert>` for errors.

fastapi-users login endpoint: `POST /auth/login` with form-urlencoded body `username=<email>&password=<pw>` (OAuth2PasswordRequestForm). The endpoint returns 204 on success.

Note: fastapi-users cookie login uses `application/x-www-form-urlencoded` not JSON.

- [ ] **Step 1: Update `users.ts` login to use form encoding**

In `frontend/src/lib/api/endpoints/users.ts`, replace the `login` implementation:

```ts
/** Log in with email+password. Sets auth cookie. Returns 204. */
login(credentials: { username: string; password: string }): Promise<void> {
    // fastapi-users uses OAuth2 form encoding
    const body = new URLSearchParams(credentials).toString();
    return req('POST_FORM', '/auth/login', { rawBody: body, contentType: 'application/x-www-form-urlencoded' });
},
```

However `Requester` currently only supports JSON. We need to extend it to support raw body + custom content-type. Update `client.ts` `RequestOptions`:

```ts
interface RequestOptions {
    query?: object;
    body?: unknown;
    rawBody?: string;
    contentType?: string;
    requireAuth?: boolean;
    signal?: AbortSignal;
}
```

And in `createRequester`, update headers + body:

```ts
if (opts.contentType) {
    headers['Content-Type'] = opts.contentType;
} else if (body !== undefined) {
    headers['Content-Type'] = 'application/json';
}
// ...
body: opts.rawBody ?? (body !== undefined ? JSON.stringify(body) : undefined),
```

Update the `login` call in `users.ts` to use the standard `req` signature:

```ts
login(creds: { username: string; password: string }): Promise<void> {
    const rawBody = new URLSearchParams(creds).toString();
    return req('POST', '/auth/login', { rawBody, contentType: 'application/x-www-form-urlencoded' });
},
```

- [ ] **Step 2: Create login page**

```svelte
<!-- frontend/src/routes/login/+page.svelte -->
<script lang="ts">
    import { goto } from '$app/navigation';
    import { Alert, AlertDescription } from '$lib/components/ui/alert';
    import { Button } from '$lib/components/ui/button';
    import { Input } from '$lib/components/ui/input';
    import { Label } from '$lib/components/ui/label';
    import { createApiClient } from '$lib/api';
    import { getErrorMessage } from '$lib/api/errors';
    import { currentUser } from '$lib/auth/currentUser.svelte';

    let email = $state('');
    let password = $state('');
    let emailTouched = $state(false);
    let loading = $state(false);
    let errorMessage = $state<string | null>(null);

    const emailValid = $derived(email.includes('@') && email.length > 3);
    const passwordValid = $derived(password.length > 0);
    const canSubmit = $derived(emailValid && passwordValid && !loading);

    async function handleSubmit(e: SubmitEvent) {
        e.preventDefault();
        if (!canSubmit) return;
        loading = true;
        errorMessage = null;
        try {
            const api = createApiClient({ cookieAuth: true });
            await api.login({ username: email, password });
            const user = await api.getMe();
            currentUser.set(user);
            await goto('/profile/account');
        } catch (err) {
            errorMessage = getErrorMessage(err, {
                unauthorized: 'Felaktig e-postadress eller lösenord.',
                bad_request: 'Felaktig e-postadress eller lösenord.'
            });
        } finally {
            loading = false;
        }
    }
</script>

<svelte:head>
    <title>Logga in – Golfkompis</title>
</svelte:head>

<main class="mx-auto max-w-sm px-4 py-16">
    <h1 class="mb-6 text-2xl font-bold">Logga in</h1>

    <form class="flex flex-col gap-4" onsubmit={handleSubmit}>
        {#if errorMessage}
            <Alert variant="destructive">
                <AlertDescription>{errorMessage}</AlertDescription>
            </Alert>
        {/if}

        <div class="flex flex-col gap-1.5">
            <Label for="email">E-postadress</Label>
            <Input
                id="email"
                type="email"
                autocomplete="email"
                bind:value={email}
                onblur={() => (emailTouched = true)}
                aria-invalid={emailTouched && !emailValid}
                aria-describedby={emailTouched && !emailValid ? 'email-error' : undefined}
            />
            {#if emailTouched && !emailValid}
                <p id="email-error" class="text-destructive text-xs">Ange en giltig e-postadress.</p>
            {/if}
        </div>

        <div class="flex flex-col gap-1.5">
            <Label for="password">Lösenord</Label>
            <Input
                id="password"
                type="password"
                autocomplete="current-password"
                bind:value={password}
            />
        </div>

        <!-- eslint-disable-next-line svelte/no-navigation-without-resolve -->
        <p class="text-muted-foreground text-sm">
            <a href="/forgot-password" class="underline underline-offset-4">Glömt lösenordet?</a>
        </p>

        <Button type="submit" disabled={!canSubmit}>
            {#if loading}Loggar in…{:else}Logga in{/if}
        </Button>

        <!-- eslint-disable-next-line svelte/no-navigation-without-resolve -->
        <p class="text-muted-foreground text-center text-sm">
            Inget konto? <a href="/register" class="underline underline-offset-4">Registrera dig</a>
        </p>
    </form>
</main>
```

- [ ] **Step 3: Verify types**

```sh
cd frontend && pnpm check
```
Expected: 0 errors.

- [ ] **Step 4: Commit**

```sh
git add frontend/src/routes/login/+page.svelte frontend/src/lib/api/endpoints/users.ts frontend/src/lib/api/client.ts
git commit -m "feat: add /login page with form-encoded cookie auth"
```

---

## Task 7: Register page (`/register`)

**Files:**
- Create: `frontend/src/routes/register/+page.svelte`

Register → show success message ("Kolla din e-post för en verifieringslänk."), no auto-login.

- [ ] **Step 1: Create register page**

```svelte
<!-- frontend/src/routes/register/+page.svelte -->
<script lang="ts">
    import { Alert, AlertDescription } from '$lib/components/ui/alert';
    import { Button } from '$lib/components/ui/button';
    import { Input } from '$lib/components/ui/input';
    import { Label } from '$lib/components/ui/label';
    import { createApiClient } from '$lib/api';
    import { getErrorMessage } from '$lib/api/errors';

    let email = $state('');
    let password = $state('');
    let password2 = $state('');
    let emailTouched = $state(false);
    let password2Touched = $state(false);
    let loading = $state(false);
    let errorMessage = $state<string | null>(null);
    let success = $state(false);

    const emailValid = $derived(email.includes('@') && email.length > 3);
    const passwordValid = $derived(password.length >= 8);
    const passwordsMatch = $derived(password === password2);
    const canSubmit = $derived(emailValid && passwordValid && passwordsMatch && !loading);

    async function handleSubmit(e: SubmitEvent) {
        e.preventDefault();
        if (!canSubmit) return;
        loading = true;
        errorMessage = null;
        try {
            const api = createApiClient({ cookieAuth: true });
            await api.register({ email, password, username: null, full_name: null, age: null });
            success = true;
        } catch (err) {
            errorMessage = getErrorMessage(err, {
                conflict: 'Det finns redan ett konto med den e-postadressen.',
                bad_request: 'Kontrollera att du angett en giltig e-postadress och ett lösenord med minst 8 tecken.'
            });
        } finally {
            loading = false;
        }
    }
</script>

<svelte:head>
    <title>Registrera dig – Golfkompis</title>
</svelte:head>

<main class="mx-auto max-w-sm px-4 py-16">
    <h1 class="mb-6 text-2xl font-bold">Skapa konto</h1>

    {#if success}
        <Alert>
            <AlertDescription>
                Kolla din e-post för en verifieringslänk. Du kan logga in när du har verifierat din adress.
            </AlertDescription>
        </Alert>
        <!-- eslint-disable-next-line svelte/no-navigation-without-resolve -->
        <p class="text-muted-foreground mt-4 text-center text-sm">
            <a href="/login" class="underline underline-offset-4">Gå till inloggning</a>
        </p>
    {:else}
        <form class="flex flex-col gap-4" onsubmit={handleSubmit}>
            {#if errorMessage}
                <Alert variant="destructive">
                    <AlertDescription>{errorMessage}</AlertDescription>
                </Alert>
            {/if}

            <div class="flex flex-col gap-1.5">
                <Label for="email">E-postadress</Label>
                <Input
                    id="email"
                    type="email"
                    autocomplete="email"
                    bind:value={email}
                    onblur={() => (emailTouched = true)}
                    aria-invalid={emailTouched && !emailValid}
                />
                {#if emailTouched && !emailValid}
                    <p class="text-destructive text-xs">Ange en giltig e-postadress.</p>
                {/if}
            </div>

            <div class="flex flex-col gap-1.5">
                <Label for="password">Lösenord</Label>
                <Input
                    id="password"
                    type="password"
                    autocomplete="new-password"
                    bind:value={password}
                />
                {#if password.length > 0 && !passwordValid}
                    <p class="text-destructive text-xs">Lösenordet måste vara minst 8 tecken.</p>
                {/if}
            </div>

            <div class="flex flex-col gap-1.5">
                <Label for="password2">Bekräfta lösenord</Label>
                <Input
                    id="password2"
                    type="password"
                    autocomplete="new-password"
                    bind:value={password2}
                    onblur={() => (password2Touched = true)}
                    aria-invalid={password2Touched && !passwordsMatch}
                />
                {#if password2Touched && !passwordsMatch}
                    <p class="text-destructive text-xs">Lösenorden stämmer inte överens.</p>
                {/if}
            </div>

            <Button type="submit" disabled={!canSubmit}>
                {#if loading}Skapar konto…{:else}Skapa konto{/if}
            </Button>

            <!-- eslint-disable-next-line svelte/no-navigation-without-resolve -->
            <p class="text-muted-foreground text-center text-sm">
                Har du redan ett konto? <a href="/login" class="underline underline-offset-4">Logga in</a>
            </p>
        </form>
    {/if}
</main>
```

- [ ] **Step 2: Verify types**

```sh
cd frontend && pnpm check
```
Expected: 0 errors.

- [ ] **Step 3: Commit**

```sh
git add frontend/src/routes/register/+page.svelte
git commit -m "feat: add /register page"
```

---

## Task 8: Forgot-password page (`/forgot-password`)

**Files:**
- Create: `frontend/src/routes/forgot-password/+page.svelte`

- [ ] **Step 1: Create page**

```svelte
<!-- frontend/src/routes/forgot-password/+page.svelte -->
<script lang="ts">
    import { Alert, AlertDescription } from '$lib/components/ui/alert';
    import { Button } from '$lib/components/ui/button';
    import { Input } from '$lib/components/ui/input';
    import { Label } from '$lib/components/ui/label';
    import { createApiClient } from '$lib/api';
    import { getErrorMessage } from '$lib/api/errors';

    let email = $state('');
    let loading = $state(false);
    let errorMessage = $state<string | null>(null);
    let success = $state(false);

    const canSubmit = $derived(email.includes('@') && email.length > 3 && !loading);

    async function handleSubmit(e: SubmitEvent) {
        e.preventDefault();
        if (!canSubmit) return;
        loading = true;
        errorMessage = null;
        try {
            const api = createApiClient({ cookieAuth: true });
            await api.forgotPassword({ email });
            success = true;
        } catch (err) {
            errorMessage = getErrorMessage(err);
        } finally {
            loading = false;
        }
    }
</script>

<svelte:head>
    <title>Glömt lösenord – Golfkompis</title>
</svelte:head>

<main class="mx-auto max-w-sm px-4 py-16">
    <h1 class="mb-6 text-2xl font-bold">Glömt lösenordet?</h1>

    {#if success}
        <Alert>
            <AlertDescription>
                Om det finns ett konto med den adressen skickas en återställningslänk inom kort.
            </AlertDescription>
        </Alert>
    {:else}
        <form class="flex flex-col gap-4" onsubmit={handleSubmit}>
            {#if errorMessage}
                <Alert variant="destructive">
                    <AlertDescription>{errorMessage}</AlertDescription>
                </Alert>
            {/if}

            <div class="flex flex-col gap-1.5">
                <Label for="email">E-postadress</Label>
                <Input id="email" type="email" autocomplete="email" bind:value={email} />
            </div>

            <Button type="submit" disabled={!canSubmit}>
                {#if loading}Skickar…{:else}Skicka återställningslänk{/if}
            </Button>

            <!-- eslint-disable-next-line svelte/no-navigation-without-resolve -->
            <p class="text-muted-foreground text-center text-sm">
                <a href="/login" class="underline underline-offset-4">Tillbaka till inloggning</a>
            </p>
        </form>
    {/if}
</main>
```

- [ ] **Step 2: Verify and commit**

```sh
cd frontend && pnpm check
git add frontend/src/routes/forgot-password/+page.svelte
git commit -m "feat: add /forgot-password page"
```

---

## Task 9: Reset-password page (`/reset-password`)

**Files:**
- Create: `frontend/src/routes/reset-password/+page.svelte`

Reads `?token=` from URL. The backend `POST /auth/reset-password` body: `{ token, password }`.

- [ ] **Step 1: Create page**

```svelte
<!-- frontend/src/routes/reset-password/+page.svelte -->
<script lang="ts">
    import { page } from '$app/state';
    import { goto } from '$app/navigation';
    import { Alert, AlertDescription } from '$lib/components/ui/alert';
    import { Button } from '$lib/components/ui/button';
    import { Input } from '$lib/components/ui/input';
    import { Label } from '$lib/components/ui/label';
    import { createApiClient } from '$lib/api';
    import { getErrorMessage } from '$lib/api/errors';

    const token = $derived(page.url.searchParams.get('token') ?? '');

    let password = $state('');
    let password2 = $state('');
    let password2Touched = $state(false);
    let loading = $state(false);
    let errorMessage = $state<string | null>(null);

    const passwordValid = $derived(password.length >= 8);
    const passwordsMatch = $derived(password === password2);
    const canSubmit = $derived(token.length > 0 && passwordValid && passwordsMatch && !loading);

    async function handleSubmit(e: SubmitEvent) {
        e.preventDefault();
        if (!canSubmit) return;
        loading = true;
        errorMessage = null;
        try {
            const api = createApiClient({ cookieAuth: true });
            await api.resetPassword({ token, password });
            await goto('/login?reset=1');
        } catch (err) {
            errorMessage = getErrorMessage(err, {
                bad_request: 'Länken är ogiltig eller har gått ut.',
                unknown: 'Länken är ogiltig eller har gått ut.'
            });
        } finally {
            loading = false;
        }
    }
</script>

<svelte:head>
    <title>Nytt lösenord – Golfkompis</title>
</svelte:head>

<main class="mx-auto max-w-sm px-4 py-16">
    <h1 class="mb-6 text-2xl font-bold">Välj nytt lösenord</h1>

    {#if !token}
        <Alert variant="destructive">
            <AlertDescription>Ogiltig länk. Begär en ny återställningslänk.</AlertDescription>
        </Alert>
    {:else}
        <form class="flex flex-col gap-4" onsubmit={handleSubmit}>
            {#if errorMessage}
                <Alert variant="destructive">
                    <AlertDescription>{errorMessage}</AlertDescription>
                </Alert>
            {/if}

            <div class="flex flex-col gap-1.5">
                <Label for="password">Nytt lösenord</Label>
                <Input
                    id="password"
                    type="password"
                    autocomplete="new-password"
                    bind:value={password}
                />
                {#if password.length > 0 && !passwordValid}
                    <p class="text-destructive text-xs">Lösenordet måste vara minst 8 tecken.</p>
                {/if}
            </div>

            <div class="flex flex-col gap-1.5">
                <Label for="password2">Bekräfta lösenord</Label>
                <Input
                    id="password2"
                    type="password"
                    autocomplete="new-password"
                    bind:value={password2}
                    onblur={() => (password2Touched = true)}
                    aria-invalid={password2Touched && !passwordsMatch}
                />
                {#if password2Touched && !passwordsMatch}
                    <p class="text-destructive text-xs">Lösenorden stämmer inte överens.</p>
                {/if}
            </div>

            <Button type="submit" disabled={!canSubmit}>
                {#if loading}Sparar…{:else}Spara nytt lösenord{/if}
            </Button>
        </form>
    {/if}
</main>
```

- [ ] **Step 2: Verify and commit**

```sh
cd frontend && pnpm check
git add frontend/src/routes/reset-password/+page.svelte
git commit -m "feat: add /reset-password page"
```

---

## Task 10: Email verification page (`/verify`)

**Files:**
- Create: `frontend/src/routes/verify/+page.svelte`

Reads `?token=` from URL and auto-calls `POST /auth/verify` on mount.

- [ ] **Step 1: Create page**

```svelte
<!-- frontend/src/routes/verify/+page.svelte -->
<script lang="ts">
    import { page } from '$app/state';
    import { Alert, AlertDescription } from '$lib/components/ui/alert';
    import { Button } from '$lib/components/ui/button';
    import { createApiClient } from '$lib/api';
    import { currentUser } from '$lib/auth/currentUser.svelte';

    const token = $derived(page.url.searchParams.get('token') ?? '');

    let success = $state(false);
    let errorMessage = $state<string | null>(null);

    $effect(() => {
        if (!token) {
            errorMessage = 'Ogiltig verifieringslänk.';
            return;
        }
        const api = createApiClient({ cookieAuth: true });
        api.verifyEmail({ token })
            .then((user) => {
                currentUser.set(user);
                success = true;
            })
            .catch(() => {
                errorMessage = 'Länken är ogiltig eller har redan använts.';
            });
    });
</script>

<svelte:head>
    <title>Verifiera e-post – Golfkompis</title>
</svelte:head>

<main class="mx-auto max-w-sm px-4 py-16">
    <h1 class="mb-6 text-2xl font-bold">Verifiera e-postadress</h1>

    {#if success}
        <Alert>
            <AlertDescription>Din e-postadress är verifierad! Du är nu inloggad.</AlertDescription>
        </Alert>
        <!-- eslint-disable-next-line svelte/no-navigation-without-resolve -->
        <div class="mt-4">
            <a href="/profile/account">
                <Button>Gå till kontot</Button>
            </a>
        </div>
    {:else if errorMessage}
        <Alert variant="destructive">
            <AlertDescription>{errorMessage}</AlertDescription>
        </Alert>
        <!-- eslint-disable-next-line svelte/no-navigation-without-resolve -->
        <p class="text-muted-foreground mt-4 text-sm">
            <a href="/login" class="underline underline-offset-4">Gå till inloggning</a>
        </p>
    {:else}
        <p class="text-muted-foreground text-sm">Verifierar…</p>
    {/if}
</main>
```

- [ ] **Step 2: Verify and commit**

```sh
cd frontend && pnpm check
git add frontend/src/routes/verify/+page.svelte
git commit -m "feat: add /verify page for email token verification"
```

---

## Task 11: Account settings page (`/profile/account`)

**Files:**
- Create: `frontend/src/routes/profile/account/+page.svelte`

Shows: email (read-only), username, full_name, age (editable). Separate section for "Ändra lösenord" → link to `/forgot-password`. Danger zone: delete account.

- [ ] **Step 1: Create page**

```svelte
<!-- frontend/src/routes/profile/account/+page.svelte -->
<script lang="ts">
    import { goto } from '$app/navigation';
    import { Alert, AlertDescription } from '$lib/components/ui/alert';
    import { Button } from '$lib/components/ui/button';
    import { Input } from '$lib/components/ui/input';
    import { Label } from '$lib/components/ui/label';
    import { createApiClient } from '$lib/api';
    import { getErrorMessage } from '$lib/api/errors';
    import { currentUser } from '$lib/auth/currentUser.svelte';

    let username = $state(currentUser.user?.username ?? '');
    let fullName = $state(currentUser.user?.full_name ?? '');
    let age = $state<string>(currentUser.user?.age?.toString() ?? '');

    let saving = $state(false);
    let saveError = $state<string | null>(null);
    let saveSuccess = $state(false);

    let deleting = $state(false);
    let deleteError = $state<string | null>(null);
    let confirmDelete = $state(false);

    async function handleSave(e: SubmitEvent) {
        e.preventDefault();
        saving = true;
        saveError = null;
        saveSuccess = false;
        try {
            const api = createApiClient({ cookieAuth: true });
            const updated = await api.patchMe({
                username: username || null,
                full_name: fullName || null,
                age: age ? parseInt(age, 10) : null
            });
            currentUser.set(updated);
            saveSuccess = true;
        } catch (err) {
            saveError = getErrorMessage(err, {
                conflict: 'Användarnamnet är redan taget.',
                unauthorized: 'Du är inte inloggad.'
            });
        } finally {
            saving = false;
        }
    }

    async function handleDelete() {
        deleting = true;
        deleteError = null;
        try {
            const api = createApiClient({ cookieAuth: true });
            await api.deleteMe();
            currentUser.clear();
            await goto('/');
        } catch (err) {
            deleteError = getErrorMessage(err);
            deleting = false;
        }
    }
</script>

<svelte:head>
    <title>Mitt konto – Golfkompis</title>
</svelte:head>

<main class="mx-auto max-w-lg px-4 py-12">
    <h1 class="mb-8 text-2xl font-bold">Mitt konto</h1>

    {#if !currentUser.isLoggedIn}
        <p class="text-muted-foreground mb-4">Du är inte inloggad.</p>
        <!-- eslint-disable-next-line svelte/no-navigation-without-resolve -->
        <a href="/login"><Button>Logga in</Button></a>
    {:else}
        <!-- Profile form -->
        <section class="mb-10">
            <h2 class="mb-4 text-lg font-semibold">Profiluppgifter</h2>
            <form class="flex flex-col gap-4" onsubmit={handleSave}>
                {#if saveError}
                    <Alert variant="destructive">
                        <AlertDescription>{saveError}</AlertDescription>
                    </Alert>
                {/if}
                {#if saveSuccess}
                    <Alert>
                        <AlertDescription>Dina uppgifter har sparats.</AlertDescription>
                    </Alert>
                {/if}

                <div class="flex flex-col gap-1.5">
                    <Label for="email">E-postadress</Label>
                    <Input id="email" type="email" value={currentUser.user?.email ?? ''} disabled />
                </div>

                <div class="flex flex-col gap-1.5">
                    <Label for="username">Användarnamn</Label>
                    <Input id="username" type="text" autocomplete="username" bind:value={username} />
                </div>

                <div class="flex flex-col gap-1.5">
                    <Label for="fullName">Fullständigt namn</Label>
                    <Input id="fullName" type="text" autocomplete="name" bind:value={fullName} />
                </div>

                <div class="flex flex-col gap-1.5">
                    <Label for="age">Ålder</Label>
                    <Input id="age" type="number" min="1" max="120" bind:value={age} />
                </div>

                <Button type="submit" disabled={saving}>
                    {#if saving}Sparar…{:else}Spara ändringar{/if}
                </Button>
            </form>
        </section>

        <!-- Change password -->
        <section class="mb-10">
            <h2 class="mb-2 text-lg font-semibold">Ändra lösenord</h2>
            <p class="text-muted-foreground mb-3 text-sm">
                Begär en länk via e-post för att ange ett nytt lösenord.
            </p>
            <!-- eslint-disable-next-line svelte/no-navigation-without-resolve -->
            <a href="/forgot-password">
                <Button variant="outline">Skicka återställningslänk</Button>
            </a>
        </section>

        <!-- Danger zone -->
        <section class="border-destructive rounded-lg border p-6">
            <h2 class="text-destructive mb-2 text-lg font-semibold">Radera konto</h2>
            <p class="text-muted-foreground mb-4 text-sm">
                Ditt konto och all data raderas permanent. Åtgärden kan inte ångras.
            </p>

            {#if deleteError}
                <Alert variant="destructive" class="mb-4">
                    <AlertDescription>{deleteError}</AlertDescription>
                </Alert>
            {/if}

            {#if !confirmDelete}
                <Button variant="destructive" onclick={() => (confirmDelete = true)}>
                    Radera mitt konto
                </Button>
            {:else}
                <p class="text-destructive mb-3 text-sm font-medium">
                    Är du säker? Det går inte att ångra.
                </p>
                <div class="flex gap-3">
                    <Button variant="destructive" onclick={handleDelete} disabled={deleting}>
                        {#if deleting}Raderar…{:else}Ja, radera{/if}
                    </Button>
                    <Button variant="outline" onclick={() => (confirmDelete = false)}>Avbryt</Button>
                </div>
            {/if}
        </section>
    {/if}
</main>
```

- [ ] **Step 2: Verify and commit**

```sh
cd frontend && pnpm check
git add frontend/src/routes/profile/account/+page.svelte
git commit -m "feat: add /profile/account settings page"
```

---

## Task 12: Component tests

**Files:**
- Create: `frontend/src/routes/login/login.svelte.test.ts`

- [ ] **Step 1: Write component test for login page**

```ts
// frontend/src/routes/login/login.svelte.test.ts
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render } from 'vitest-browser-svelte';
import { userEvent } from '@testing-library/user-event';
import LoginPage from './+page.svelte';

// Mock the API module
vi.mock('$lib/api', () => ({
    createApiClient: vi.fn()
}));
vi.mock('$app/navigation', () => ({ goto: vi.fn() }));

import { createApiClient } from '$lib/api';
import { goto } from '$app/navigation';

describe('Login page', () => {
    beforeEach(() => {
        vi.clearAllMocks();
    });

    it('submit button disabled when fields empty', async () => {
        const { getByRole } = render(LoginPage);
        const btn = getByRole('button', { name: /logga in/i });
        expect(btn).toBeDisabled();
    });

    it('shows error on bad credentials', async () => {
        const mockApi = {
            login: vi.fn().mockRejectedValue(Object.assign(new Error('Unauthorized'), { code: 'unauthorized', status: 401 })),
            getMe: vi.fn()
        };
        vi.mocked(createApiClient).mockReturnValue(mockApi as never);

        const { getByLabelText, findByText } = render(LoginPage);
        const user = userEvent.setup();

        await user.type(getByLabelText(/e-postadress/i), 'a@b.com');
        await user.type(getByLabelText(/lösenord/i), 'wrongpw');
        await user.click(document.querySelector('button[type="submit"]')!);

        await findByText(/felaktig e-postadress eller lösenord/i);
    });
});
```

- [ ] **Step 2: Run component tests**

```sh
cd frontend && pnpm test --run --project=client src/routes/login/login.svelte.test.ts
```
Expected: PASS (or adjust mocks if needed).

- [ ] **Step 3: Commit**

```sh
git add frontend/src/routes/login/login.svelte.test.ts
git commit -m "test: add login page component test"
```

---

## Task 13: Final verification

- [ ] **Step 1: Type-check**

```sh
cd frontend && pnpm check
```
Expected: 0 errors.

- [ ] **Step 2: Lint**

```sh
cd frontend && pnpm lint
```
Expected: 0 warnings/errors.

- [ ] **Step 3: All tests**

```sh
cd frontend && pnpm test --run
```
Expected: all pass.

- [ ] **Step 4: Commit if any lint fixes needed**

```sh
git add -A && git commit -m "chore: lint fixes for user auth frontend"
```

---

## Self-Review

**Spec coverage:**
- ✅ `/login`, `/register`, `/forgot-password`, `/reset-password`, `/verify`, `/profile/account` routes
- ✅ `currentUser` store (Task 3)
- ✅ Boot-time `/users/me` check (Task 4)
- ✅ Navbar updated (Task 5)
- ✅ Vite proxy for `/auth/*`, `/users/*` (Task 1)
- ✅ API endpoint module with all fastapi-users routes (Task 2)
- ✅ `credentials: 'include'` via `cookieAuth` flag (Task 2)
- ✅ Form validation matches CredentialsForm pattern (Tasks 6–11)
- ✅ Swedish text throughout
- ✅ Component test (Task 12)
- ✅ No toast library — inline Alert only
- ✅ Logout does NOT affect MinGolf credentials
- ✅ Register → success message, no auto-login

**Known gap:** No Playwright e2e test (originally planned). Backend must be running for e2e, and the plan doesn't spin up a test server. Omitted intentionally — add as follow-up if needed.

**Type consistency check:**
- `AppUser` defined once in `users.ts`, imported in `currentUser.svelte.ts` ✅
- `createApiClient({ cookieAuth: true })` — `cookieAuth` added to `ApiConfig` in Task 2 ✅
- `api.login`, `api.getMe`, `api.patchMe`, `api.deleteMe`, `api.forgotPassword`, `api.resetPassword`, `api.requestVerify`, `api.verifyEmail`, `api.register` — all defined in `users.ts` ✅
- `PATCH /users/me` — fastapi-users uses PATCH for user update ✅
- `DELETE /users/me` — fastapi-users supports this endpoint ✅
