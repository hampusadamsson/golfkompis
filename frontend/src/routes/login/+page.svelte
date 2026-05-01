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
			const api = createApiClient();
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
				<p id="email-error" class="text-xs text-destructive">Ange en giltig e-postadress.</p>
			{/if}
		</div>

		<div class="flex flex-col gap-1.5">
			<Label for="password">Lösenord</Label>
			<Input id="password" type="password" autocomplete="current-password" bind:value={password} />
		</div>

		<!-- eslint-disable-next-line svelte/no-navigation-without-resolve -->
		<p class="text-sm text-muted-foreground">
			<a href="/forgot-password" class="underline underline-offset-4">Glömt lösenordet?</a>
		</p>

		<Button type="submit" disabled={!canSubmit}>
			{#if loading}Loggar in…{:else}Logga in{/if}
		</Button>

		<!-- eslint-disable-next-line svelte/no-navigation-without-resolve -->
		<p class="text-center text-sm text-muted-foreground">
			Inget konto? <a href="/register" class="underline underline-offset-4">Registrera dig</a>
		</p>
	</form>
</main>
