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
