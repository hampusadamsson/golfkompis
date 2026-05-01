# MinGolf Credentials on Account + Remove Age Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Store MinGolf username and password (plaintext) on the user model so they persist server-side, surface them as editable optional fields in `/profile/account`, and remove `age` everywhere.

**Architecture:** Add two nullable columns (`mingolf_username`, `mingolf_password`) to the SQLAlchemy `User` model and corresponding Pydantic schemas. The frontend edits them via the existing PATCH `/users/me` endpoint. On successful save, the local `credentials` store is also updated so MinGolf features work immediately. Age is deleted from model, schemas, and frontend.

**Tech Stack:** Python/FastAPI/SQLAlchemy (aiosqlite), fastapi-users, SvelteKit 5 runes, TypeScript

---

## File Map

| File | Change |
|---|---|
| `backend/src/golfkompis/users/models.py` | Add `mingolf_username`, `mingolf_password` columns; remove `age` |
| `backend/src/golfkompis/users/schemas.py` | Add `mingolf_username`, `mingolf_password` fields; remove `age` |
| `backend/src/tests/test_auth_routes.py` | Update register test (remove age); add patch-mingolf-creds test |
| `backend/users.db` | Delete (recreate on next startup) |
| `frontend/src/lib/api/endpoints/users.ts` | Add `mingolf_username`, `mingolf_password` to interfaces; remove `age` |
| `frontend/src/routes/profile/account/+page.svelte` | Add MinGolf section; remove age field |

---

### Task 1: Backend model — add mingolf columns, remove age

**Files:**
- Modify: `backend/src/golfkompis/users/models.py`

- [ ] **Step 1: Write the updated model**

Replace the file content:

```python
"""SQLAlchemy ORM models for the user-management DB."""

from fastapi_users.db import SQLAlchemyBaseUserTableUUID
from fastapi_users_db_sqlalchemy.access_token import SQLAlchemyBaseAccessTokenTableUUID
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from golfkompis.users.db import Base


class User(SQLAlchemyBaseUserTableUUID, Base):
    username: Mapped[str | None] = mapped_column(
        String(length=64), unique=True, index=True, nullable=True, default=None
    )
    full_name: Mapped[str | None] = mapped_column(
        String(length=128), nullable=True, default=None
    )
    mingolf_username: Mapped[str | None] = mapped_column(
        String(length=32), nullable=True, default=None
    )
    mingolf_password: Mapped[str | None] = mapped_column(
        String(length=256), nullable=True, default=None
    )


class AccessToken(SQLAlchemyBaseAccessTokenTableUUID, Base):
    pass
```

Note: `Integer` import removed (no longer needed), `age` column gone.

- [ ] **Step 2: Delete the stale database**

```bash
rm -f backend/users.db
```

- [ ] **Step 3: Verify ruff + basedpyright**

```bash
cd backend
uv run ruff check src/
uv run basedpyright
```

Expected: 0 errors (except the pre-existing `_spa_fallback` basedpyright warning which is acceptable).

---

### Task 2: Backend schemas — add mingolf fields, remove age

**Files:**
- Modify: `backend/src/golfkompis/users/schemas.py`

- [ ] **Step 1: Write the failing test**

Add to `backend/src/tests/test_auth_routes.py` after the existing `test_patch_me` test:

```python
@pytest.mark.asyncio
async def test_patch_mingolf_creds(async_client: AsyncClient) -> None:
    """PATCH /users/me can set mingolf_username and mingolf_password."""
    # register + login
    await async_client.post(
        "/auth/register", json={"email": "mg@test.com", "password": "secret1234"}
    )
    await async_client.post(
        "/auth/login",
        data={"username": "mg@test.com", "password": "secret1234"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    resp = await async_client.patch(
        "/users/me",
        json={"mingolf_username": "123456-789", "mingolf_password": "mypass"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["mingolf_username"] == "123456-789"
    # password is returned (plaintext, by design)
    assert data["mingolf_password"] == "mypass"
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd backend
uv run pytest src/tests/test_auth_routes.py::test_patch_mingolf_creds -v
```

Expected: FAIL — `mingolf_username` not in response (422 or missing field).

- [ ] **Step 3: Update schemas**

Replace `backend/src/golfkompis/users/schemas.py`:

```python
"""Pydantic schemas for fastapi-users endpoints."""

import uuid

from fastapi_users import schemas


class UserRead(schemas.BaseUser[uuid.UUID]):
    username: str | None = None
    full_name: str | None = None
    mingolf_username: str | None = None
    mingolf_password: str | None = None


class UserCreate(schemas.BaseUserCreate):
    username: str | None = None
    full_name: str | None = None


class UserUpdate(schemas.BaseUserUpdate):
    username: str | None = None
    full_name: str | None = None
    mingolf_username: str | None = None
    mingolf_password: str | None = None
```

Note: `Field` import and `age` gone everywhere. `mingolf_password` intentionally returned in `UserRead` (plaintext, by design decision).

- [ ] **Step 4: Run test to verify it passes**

```bash
cd backend
uv run pytest src/tests/test_auth_routes.py::test_patch_mingolf_creds -v
```

Expected: PASS.

- [ ] **Step 5: Also update the existing register test — it sends age which is now gone**

Open `backend/src/tests/test_auth_routes.py`. Find `test_register`. It likely sends `{"email": ..., "password": ..., ...}` — verify no `age` field is in the JSON body. If it is, remove it.

- [ ] **Step 6: Run all backend tests**

```bash
cd backend
uv run pytest -q
```

Expected: all pass (52 or more).

- [ ] **Step 7: Commit**

```bash
cd backend
git add src/golfkompis/users/models.py src/golfkompis/users/schemas.py src/tests/test_auth_routes.py
git commit -m "feat: add mingolf_username/password to user model and schemas, remove age"
```

---

### Task 3: Frontend types + API client — add mingolf fields, remove age

**Files:**
- Modify: `frontend/src/lib/api/endpoints/users.ts`

- [ ] **Step 1: Write the updated file**

```typescript
import type { Requester } from '../client.js';

export interface AppUser {
	id: string;
	email: string;
	is_active: boolean;
	is_superuser: boolean;
	is_verified: boolean;
	username: string | null;
	full_name: string | null;
	mingolf_username: string | null;
	mingolf_password: string | null;
}

export interface UserCreate {
	email: string;
	password: string;
	username: string | null;
	full_name: string | null;
}

export interface UserUpdate {
	username?: string | null;
	full_name?: string | null;
	mingolf_username?: string | null;
	mingolf_password?: string | null;
}

export function users(req: Requester) {
	return {
		register(body: UserCreate): Promise<AppUser> {
			return req('POST', '/auth/register', { body });
		},
		login(creds: { username: string; password: string }): Promise<void> {
			const rawBody = new URLSearchParams(creds).toString();
			return req('POST', '/auth/login', {
				rawBody,
				contentType: 'application/x-www-form-urlencoded'
			});
		},
		logout(): Promise<void> {
			return req('POST', '/auth/logout', {});
		},
		getMe(): Promise<AppUser> {
			return req('GET', '/users/me', {});
		},
		patchMe(body: UserUpdate): Promise<AppUser> {
			return req('PATCH', '/users/me', { body });
		},
		deleteMe(): Promise<void> {
			return req('DELETE', '/users/me', {});
		},
		forgotPassword(body: { email: string }): Promise<void> {
			return req('POST', '/auth/forgot-password', { body });
		},
		resetPassword(body: { token: string; password: string }): Promise<void> {
			return req('POST', '/auth/reset-password', { body });
		},
		requestVerify(body: { email: string }): Promise<void> {
			return req('POST', '/auth/request-verify-token', { body });
		},
		verifyEmail(body: { token: string }): Promise<AppUser> {
			return req('POST', '/auth/verify', { body });
		}
	};
}
```

- [ ] **Step 2: Run type check**

```bash
cd frontend
pnpm check
```

Expected: 0 errors (any error about `age` being used elsewhere in the codebase will surface here — fix those too before committing).

- [ ] **Step 3: Fix any age references that surface**

If `pnpm check` flags `age` references in other files (e.g. `currentUser.svelte.ts`, `+layout.svelte`, login/register pages):
- Remove `age` property reads/writes from those files.
- `currentUser.svelte.ts` likely just stores the `AppUser` object; since `AppUser` no longer has `age`, no action needed unless it explicitly reads `.age`.

- [ ] **Step 4: Commit**

```bash
cd frontend
git add src/lib/api/endpoints/users.ts
git commit -m "feat: update AppUser/UserUpdate types — add mingolf fields, remove age"
```

---

### Task 4: Frontend account page — add MinGolf section, remove age field

**Files:**
- Modify: `frontend/src/routes/profile/account/+page.svelte`

Current state of the file (as of last commit):
- `<script>`: imports `Alert/AlertDescription`, `Button`, `Input`, `Label`, `createApiClient`, `getErrorMessage`, `currentUser`; states: `username`, `fullName`, `age`, `saving`, `saveError`, `saveSuccess`; handler: `handleSave` (calls `patchMe({username, full_name, age})`).
- Template: email (disabled), username, full_name, age inputs + save button; change-password section.

- [ ] **Step 1: Write the updated page**

Replace `frontend/src/routes/profile/account/+page.svelte` with:

```svelte
<script lang="ts">
	import { Alert, AlertDescription } from '$lib/components/ui/alert';
	import { Button } from '$lib/components/ui/button';
	import { Input } from '$lib/components/ui/input';
	import { Label } from '$lib/components/ui/label';
	import { createApiClient } from '$lib/api';
	import { getErrorMessage } from '$lib/api/errors';
	import { currentUser } from '$lib/auth/currentUser.svelte';
	import { credentials } from '$lib/auth/credentials.svelte';
	import { formatGolfId, isValidGolfId } from '$lib/auth/golfId';

	// --- Profile fields ---
	let username = $state(currentUser.user?.username ?? '');
	let fullName = $state(currentUser.user?.full_name ?? '');

	let saving = $state(false);
	let saveError = $state<string | null>(null);
	let saveSuccess = $state(false);

	// --- MinGolf credentials ---
	let mingolfUsername = $state(currentUser.user?.mingolf_username ?? credentials.username ?? '');
	let mingolfPassword = $state(currentUser.user?.mingolf_password ?? credentials.password ?? '');
	let mingolfShowPassword = $state(false);
	let mingolfSaving = $state(false);
	let mingolfError = $state<string | null>(null);
	let mingolfSuccess = $state(false);

	const mingolfUsernameValid = $derived(
		mingolfUsername === '' || isValidGolfId(mingolfUsername)
	);

	async function handleSave(e: SubmitEvent) {
		e.preventDefault();
		saving = true;
		saveError = null;
		saveSuccess = false;
		try {
			const api = createApiClient({ cookieAuth: true });
			const updated = await api.patchMe({
				username: username || null,
				full_name: fullName || null
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

	async function handleMingolfSave(e: SubmitEvent) {
		e.preventDefault();
		mingolfSaving = true;
		mingolfError = null;
		mingolfSuccess = false;
		try {
			const api = createApiClient({ cookieAuth: true });
			const updated = await api.patchMe({
				mingolf_username: mingolfUsername || null,
				mingolf_password: mingolfPassword || null
			});
			currentUser.set(updated);
			// Also sync the local credentials store so MinGolf features work
			if (updated.mingolf_username && updated.mingolf_password) {
				const profileApi = createApiClient({
					credentials: {
						username: updated.mingolf_username,
						password: updated.mingolf_password
					}
				});
				try {
					const profile = await profileApi.getProfile();
					credentials.set(updated.mingolf_username, updated.mingolf_password, profile, true);
				} catch {
					// Creds saved to account but MinGolf verification failed; don't block success
				}
			} else {
				credentials.clear();
			}
			mingolfSuccess = true;
		} catch (err) {
			mingolfError = getErrorMessage(err, {
				unauthorized: 'Du är inte inloggad.'
			});
		} finally {
			mingolfSaving = false;
		}
	}

	function handleMingolfUsernameInput(e: Event) {
		const target = e.target as HTMLInputElement;
		mingolfUsername = formatGolfId(target.value);
	}
</script>

<svelte:head>
	<title>Mitt konto – Golfkompis</title>
</svelte:head>

<main class="mx-auto max-w-lg px-4 py-12">
	<h1 class="mb-8 text-2xl font-bold">Mitt konto</h1>

	{#if !currentUser.isLoggedIn}
		<p class="mb-4 text-muted-foreground">Du är inte inloggad.</p>
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

				<Button type="submit" disabled={saving}>
					{#if saving}Sparar…{:else}Spara ändringar{/if}
				</Button>
			</form>
		</section>

		<!-- MinGolf credentials -->
		<section class="mb-10">
			<h2 class="mb-2 text-lg font-semibold">MinGolf-koppling</h2>
			<p class="mb-3 text-sm text-muted-foreground">
				Valfritt. Krävs för att boka tider och se historik.
			</p>
			<form class="flex flex-col gap-4" onsubmit={handleMingolfSave}>
				{#if mingolfError}
					<Alert variant="destructive">
						<AlertDescription>{mingolfError}</AlertDescription>
					</Alert>
				{/if}
				{#if mingolfSuccess}
					<Alert>
						<AlertDescription>MinGolf-uppgifter sparade.</AlertDescription>
					</Alert>
				{/if}

				<div class="flex flex-col gap-1.5">
					<Label for="mingolfUsername">Golf-ID</Label>
					<Input
						id="mingolfUsername"
						type="text"
						inputmode="numeric"
						autocomplete="username"
						placeholder="123456-789"
						value={mingolfUsername}
						oninput={handleMingolfUsernameInput}
						aria-invalid={mingolfUsername !== '' && !mingolfUsernameValid}
					/>
					{#if mingolfUsername !== '' && !mingolfUsernameValid}
						<p class="text-xs text-destructive">Format: 123456-789</p>
					{/if}
				</div>

				<div class="flex flex-col gap-1.5">
					<Label for="mingolfPassword">Lösenord</Label>
					<div class="relative">
						<Input
							id="mingolfPassword"
							type={mingolfShowPassword ? 'text' : 'password'}
							autocomplete="current-password"
							bind:value={mingolfPassword}
							class="pr-10"
						/>
						<button
							type="button"
							class="absolute right-2 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
							onclick={() => (mingolfShowPassword = !mingolfShowPassword)}
							aria-label={mingolfShowPassword ? 'Dölj lösenord' : 'Visa lösenord'}
						>
							{#if mingolfShowPassword}
								<span class="text-xs">Dölj</span>
							{:else}
								<span class="text-xs">Visa</span>
							{/if}
						</button>
					</div>
				</div>

				<Button type="submit" disabled={mingolfSaving || (mingolfUsername !== '' && !mingolfUsernameValid)}>
					{#if mingolfSaving}Sparar…{:else}Spara MinGolf-uppgifter{/if}
				</Button>
			</form>
		</section>

		<!-- Change password -->
		<section class="mb-10">
			<h2 class="mb-2 text-lg font-semibold">Ändra lösenord</h2>
			<p class="mb-3 text-sm text-muted-foreground">
				Begär en länk via e-post för att ange ett nytt lösenord.
			</p>
			<!-- eslint-disable-next-line svelte/no-navigation-without-resolve -->
			<a href="/forgot-password">
				<Button variant="outline">Skicka återställningslänk</Button>
			</a>
		</section>
	{/if}
</main>
```

- [ ] **Step 2: Run type check**

```bash
cd frontend
pnpm check
```

Expected: 0 errors.

- [ ] **Step 3: Run tests**

```bash
cd frontend
pnpm test
```

Expected: all pass (no test directly references the age field or the account page form).

- [ ] **Step 4: Commit**

```bash
cd frontend
git add src/routes/profile/account/+page.svelte src/lib/api/endpoints/users.ts
git commit -m "feat: add MinGolf credentials to /profile/account, remove age"
```

---

### Task 5: Final verification

- [ ] **Step 1: Backend full suite**

```bash
cd backend
uv run ruff check src/ && uv run ruff format --check src/ && uv run basedpyright && uv run pytest -q
```

Expected: 0 lint/format/type errors, all tests pass.

- [ ] **Step 2: Frontend full suite**

```bash
cd frontend
pnpm check && pnpm test
```

Expected: 0 errors, all tests pass.

- [ ] **Step 3: Manual smoke test**
1. Start backend: `cd backend && uv run uvicorn golfkompis.app:app --reload`
2. Start frontend: `cd frontend && pnpm dev`
3. Navigate to `http://localhost:5173/profile/account` (logged in).
4. Enter a valid Golf-ID + password in the MinGolf section, save.
5. Reload the page — values should persist (fetched from `/users/me`).
6. Navigate to `/book` — should show booking UI (not the "enter credentials" form) since `credentials` store was populated.

---

## Self-Review Checklist

**Spec coverage:**
- ✅ `mingolf_username` field — model + schema + API types + form
- ✅ `mingolf_password` field — model + schema + API types + form (shown plain, no encryption)
- ✅ Both fields optional (nullable throughout)
- ✅ `age` removed from model, schemas, API types, form
- ✅ Saving MinGolf creds also hydrates the local `credentials` store
- ✅ Golf-ID format validation (reuses `isValidGolfId`/`formatGolfId`)
- ✅ Show/hide password toggle
- ✅ Stale `users.db` deleted so schema is recreated

**Placeholder scan:** None found.

**Type consistency:**
- `mingolf_username` / `mingolf_password` used consistently across model, `UserRead`, `UserUpdate`, `AppUser`, `UserUpdate` (TS), page state, `patchMe` call.
- `age` removed consistently everywhere — no stray references remain after Task 3 Step 3 cleanup.
