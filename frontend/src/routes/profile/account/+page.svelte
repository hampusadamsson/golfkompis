<script lang="ts">
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
			<p class="mb-3 text-sm text-muted-foreground">
				Begär en länk via e-post för att ange ett nytt lösenord.
			</p>
			<!-- eslint-disable-next-line svelte/no-navigation-without-restore -->
			<a href="/forgot-password">
				<Button variant="outline">Skicka återställningslänk</Button>
			</a>
		</section>
	{/if}
</main>
