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
				bad_request:
					'Kontrollera att du angett en giltig e-postadress och ett lösenord med minst 8 tecken.'
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
		<p class="mt-4 text-center text-sm text-muted-foreground">
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
					<p class="text-xs text-destructive">Ange en giltig e-postadress.</p>
				{/if}
			</div>

			<div class="flex flex-col gap-1.5">
				<Label for="password">Lösenord</Label>
				<Input id="password" type="password" autocomplete="new-password" bind:value={password} />
				{#if password.length > 0 && !passwordValid}
					<p class="text-xs text-destructive">Lösenordet måste vara minst 8 tecken.</p>
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
					<p class="text-xs text-destructive">Lösenorden stämmer inte överens.</p>
				{/if}
			</div>

			<Button type="submit" disabled={!canSubmit}>
				{#if loading}Skapar konto…{:else}Skapa konto{/if}
			</Button>

			<!-- eslint-disable-next-line svelte/no-navigation-without-resolve -->
			<p class="text-center text-sm text-muted-foreground">
				Har du redan ett konto? <a href="/login" class="underline underline-offset-4">Logga in</a>
			</p>
		</form>
	{/if}
</main>
