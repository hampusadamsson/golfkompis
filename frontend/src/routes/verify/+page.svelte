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
		<div class="mt-4">
			<!-- eslint-disable-next-line svelte/no-navigation-without-resolve -->
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
