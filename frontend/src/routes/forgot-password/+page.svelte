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
			const api = createApiClient();
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
			<p class="text-center text-sm text-muted-foreground">
				<a href="/login" class="underline underline-offset-4">Tillbaka till inloggning</a>
			</p>
		</form>
	{/if}
</main>
