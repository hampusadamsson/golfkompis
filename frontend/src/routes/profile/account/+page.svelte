<script lang="ts">
	import { Alert, AlertDescription } from '$lib/components/ui/alert';
	import { Button } from '$lib/components/ui/button';
	import { Input } from '$lib/components/ui/input';
	import { Label } from '$lib/components/ui/label';
	import { createApiClient } from '$lib/api';
	import { getErrorMessage } from '$lib/api/errors';
	import { currentUser } from '$lib/auth/currentUser.svelte';
	import { mingolfProfile } from '$lib/auth/mingolfProfile.svelte';
	import { formatGolfId, isValidGolfId } from '$lib/auth/golfId';
	import Profile from '$lib/components/Profile.svelte';

	// --- Profile fields ---
	let username = $state('');
	let fullName = $state('');

	let saving = $state(false);
	let saveError = $state<string | null>(null);
	let saveSuccess = $state(false);

	// --- MinGolf credentials ---
	let mingolfUsername = $state('');
	let mingolfPassword = $state('');
	let mingolfShowPassword = $state(false);
	let mingolfSaving = $state(false);
	let mingolfError = $state<string | null>(null);
	let mingolfSuccess = $state(false);

	const mingolfUsernameValid = $derived(mingolfUsername === '' || isValidGolfId(mingolfUsername));

	$effect(() => {
		const u = currentUser.user;
		if (u) {
			username = u.username ?? '';
			fullName = u.full_name ?? '';
			mingolfUsername = u.mingolf_username ?? '';
			mingolfPassword = u.mingolf_password ?? '';
		}
	});

	async function handleSave(e: SubmitEvent) {
		e.preventDefault();
		saving = true;
		saveError = null;
		saveSuccess = false;
		try {
			const api = createApiClient();
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
			const api = createApiClient();
			const updated = await api.patchMyMingolf({
				mingolf_username: mingolfUsername || null,
				mingolf_password: mingolfPassword || null
			});
			currentUser.set(updated);
			if (updated.mingolf_username) {
				await mingolfProfile.load(api);
			} else {
				mingolfProfile.clear();
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

	let mingolfDisconnecting = $state(false);

	async function handleMingolfDisconnect() {
		mingolfDisconnecting = true;
		mingolfError = null;
		try {
			const api = createApiClient();
			const updated = await api.patchMyMingolf({ mingolf_username: null, mingolf_password: null });
		currentUser.set(updated);
		mingolfProfile.clear();
		} catch (err) {
			mingolfError = getErrorMessage(err, { unauthorized: 'Du är inte inloggad.' });
		} finally {
			mingolfDisconnecting = false;
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
			<form id="profile-form" class="flex flex-col gap-4" onsubmit={handleSave}>
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
			</form>
		</section>

		<!-- MinGolf credentials -->
		<section class="mb-10">
			<h2 class="mb-2 text-lg font-semibold">MinGolf-koppling</h2>
			<p class="mb-3 text-sm text-muted-foreground">
				Valfritt. Krävs för att boka tider och se historik.
			</p>

			{#if currentUser.user?.mingolf_username}
				<!-- Linked state -->
				{#if mingolfProfile.loading}
					<p class="text-sm text-muted-foreground">Hämtar MinGolf-profil…</p>
				{:else if mingolfProfile.profile}
					<Profile />
					{#if mingolfError}
						<Alert variant="destructive" class="mt-4">
							<AlertDescription>{mingolfError}</AlertDescription>
						</Alert>
					{/if}
					<Button
						variant="outline"
						class="mt-4"
						onclick={handleMingolfDisconnect}
						disabled={mingolfDisconnecting}
					>
						{mingolfDisconnecting ? 'Kopplar från…' : 'Koppla från'}
					</Button>
				{:else if mingolfProfile.error}
					<Alert variant="destructive" class="mb-4">
						<AlertDescription>{mingolfProfile.error}</AlertDescription>
					</Alert>
					<Button
						variant="outline"
						onclick={handleMingolfDisconnect}
						disabled={mingolfDisconnecting}
					>
						{mingolfDisconnecting ? 'Kopplar från…' : 'Koppla från'}
					</Button>
				{/if}
			{:else}
				<!-- Not linked state — show credential form -->
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
								class="absolute top-1/2 right-2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
								onclick={() => (mingolfShowPassword = !mingolfShowPassword)}
								aria-label={mingolfShowPassword ? 'Dölj lösenord' : 'Visa lösenord'}
							>
								<span class="text-xs">{mingolfShowPassword ? 'Dölj' : 'Visa'}</span>
							</button>
						</div>
					</div>

					<Button
						type="submit"
						disabled={mingolfSaving || (mingolfUsername !== '' && !mingolfUsernameValid)}
					>
						{#if mingolfSaving}Kopplar…{:else}Koppla MinGolf{/if}
					</Button>
				</form>
			{/if}
		</section>

		<!-- Save profile button — below MinGolf section -->
		<div class="mb-10 flex flex-col gap-4">
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
			<Button type="submit" form="profile-form" disabled={saving}>
				{#if saving}Sparar…{:else}Spara ändringar{/if}
			</Button>
		</div>

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
