<script lang="ts">
	import { goto } from '$app/navigation';
	import { page } from '$app/state';
	import { Alert, AlertDescription } from '$lib/components/ui/alert';
	import { Button } from '$lib/components/ui/button';
	import { Input } from '$lib/components/ui/input';
	import { Label } from '$lib/components/ui/label';
	import { createApiClient } from '$lib/api';
	import { getErrorMessage, ApiError } from '$lib/api/errors';
	import { currentUser } from '$lib/auth/currentUser.svelte';
	import { mingolfProfile } from '$lib/auth/mingolfProfile.svelte';

	const justVerified = $derived(page.url.searchParams.get('verified') === '1');

	let email = $state('');
	let password = $state('');
	let emailTouched = $state(false);
	let loading = $state(false);
	let errorMessage = $state<string | null>(null);
	let notVerified = $state(false);

	const emailValid = $derived(email.includes('@') && email.length > 3);
	const passwordValid = $derived(password.length > 0);
	const canSubmit = $derived(emailValid && passwordValid && !loading);

	async function handleSubmit(e: SubmitEvent) {
		e.preventDefault();
		if (!canSubmit) return;
		loading = true;
		errorMessage = null;
		notVerified = false;
		try {
			const api = createApiClient();
			await api.login({ username: email, password });
			const user = await api.getMe();
			currentUser.set(user);
			if (user.mingolf_username) {
				mingolfProfile.load(api); // fire-and-forget
			}
			await goto('/profile/account');
		} catch (err) {
			if (err instanceof ApiError && err.message === 'LOGIN_USER_NOT_VERIFIED') {
				notVerified = true;
			} else {
				errorMessage = getErrorMessage(err, {
					unauthorized: 'Felaktig e-postadress eller lösenord.',
					bad_request: 'Felaktig e-postadress eller lösenord.'
				});
			}
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
		{#if justVerified}
			<Alert>
				<AlertDescription>E-postadressen är verifierad. Logga in för att fortsätta.</AlertDescription>
			</Alert>
		{/if}
		{#if notVerified}
			<Alert variant="destructive">
				<AlertDescription>
					E-postadressen är inte verifierad. Klicka på länken i e-postmeddelandet vi skickade, eller
					<button
						type="button"
						class="underline underline-offset-4"
						onclick={async () => {
							if (!email) return;
							try {
								await createApiClient().requestVerify({ email });
							} catch {
								// ignore — we don't enumerate whether the address exists
							}
							notVerified = false;
							errorMessage = 'En ny verifieringslänk har skickats.';
						}}
					>skicka ny länk</button>.
				</AlertDescription>
			</Alert>
		{/if}
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
