<script lang="ts">
	import { Alert, AlertDescription } from '$lib/components/ui/alert';
	import { Button } from '$lib/components/ui/button';
	import {
		Card,
		CardContent,
		CardDescription,
		CardFooter,
		CardHeader,
		CardTitle
	} from '$lib/components/ui/card';
	import { Checkbox } from '$lib/components/ui/checkbox';
	import { Input } from '$lib/components/ui/input';
	import { Label } from '$lib/components/ui/label';
	import EyeIcon from '@lucide/svelte/icons/eye';
	import EyeOffIcon from '@lucide/svelte/icons/eye-off';
	import Loader2Icon from '@lucide/svelte/icons/loader-2';
	import TriangleAlertIcon from '@lucide/svelte/icons/triangle-alert';

	import { createApiClient, ApiError, getErrorMessage } from '$lib/api';
	import type { Profile } from '$lib/api';
	import { credentials } from '$lib/auth/credentials.svelte';
	import { formatGolfId, isValidGolfId } from '$lib/auth/golfId';

	interface Props {
		/**
		 * Base URL of the golfkompis API used to verify credentials.
		 * @default 'http://localhost:8000'
		 */
		apiBaseUrl?: string;
		/**
		 * Called after credentials are verified successfully against `/api/v1/profile`.
		 * Receives the saved credentials and the returned profile.
		 */
		onSubmit?: (creds: { username: string; password: string }, profile: Profile) => void;
		/**
		 * Show the "Remember on this device" checkbox. Default: true.
		 */
		allowPersist?: boolean;
	/**
	 * Label for the submit button. Default: 'Logga in'.
	 */
	submitLabel?: string;
}

	let { apiBaseUrl = '', onSubmit, allowPersist = true, submitLabel = 'Logga in' }: Props = $props();

	// ── Form state ──────────────────────────────────────────────────────────
	let username = $state(credentials.username);
	let password = $state('');
	let persist = $state(credentials.isPersisted);
	let showPassword = $state(false);

	let usernameTouched = $state(false);
	let passwordTouched = $state(false);

	let loading = $state(false);
	let errorMessage = $state<string | null>(null);

	// ── Derived ─────────────────────────────────────────────────────────────
	const usernameValid = $derived(isValidGolfId(username));
	const passwordValid = $derived(password.length > 0);
	const canSubmit = $derived(usernameValid && passwordValid && !loading);

	// ── Handlers ─────────────────────────────────────────────────────────────
	function handleUsernameInput(e: Event) {
		username = formatGolfId((e.target as HTMLInputElement).value);
	}

	async function handleSubmit(e: SubmitEvent) {
		e.preventDefault();
		if (!canSubmit) return;

		loading = true;
		errorMessage = null;

		try {
			const api = createApiClient({
				baseUrl: apiBaseUrl,
				credentials: { username, password }
			});
			const profile = await api.getProfile();

			credentials.set(username, password, profile, persist);
			onSubmit?.({ username, password }, profile);
		} catch (err) {
			errorMessage = getErrorMessage(err, {
				unauthorized: 'Felaktigt Golf-ID eller lösenord. Försök igen.',
			});
		} finally {
			loading = false;
		}
	}
</script>

<Card class="w-full max-w-sm">
	<CardHeader>
		<CardTitle>Logga in på MinGolf</CardTitle>
		<CardDescription>Ange ditt Golf-ID och lösenord.</CardDescription>
	</CardHeader>

	<form onsubmit={handleSubmit}>
		<CardContent class="space-y-4">
			<!-- Error banner -->
			{#if errorMessage}
				<Alert variant="destructive">
					<TriangleAlertIcon class="h-4 w-4" />
					<AlertDescription>{errorMessage}</AlertDescription>
				</Alert>
			{/if}

			<!-- Golf-ID -->
			<div class="space-y-2">
				<Label for="golfid">Golf-ID</Label>
				<Input
					id="golfid"
					name="username"
					inputmode="numeric"
					autocomplete="username"
					placeholder="123456-789"
					maxlength={10}
					value={username}
					oninput={handleUsernameInput}
					onblur={() => (usernameTouched = true)}
					aria-invalid={usernameTouched && !usernameValid}
					aria-describedby={usernameTouched && !usernameValid && username.length > 0
						? 'golfid-error'
						: undefined}
				/>
				{#if usernameTouched && !usernameValid && username.length > 0}
				<p id="golfid-error" class="text-sm text-destructive">
					Format: 123456-789 (6 siffror, bindestreck, 3 siffror)
				</p>
				{/if}
			</div>

			<!-- Password -->
			<div class="space-y-2">
				<Label for="password">Lösenord</Label>
				<div class="relative">
					<Input
						id="password"
						name="password"
						type={showPassword ? 'text' : 'password'}
						autocomplete="current-password"
						bind:value={password}
						onblur={() => (passwordTouched = true)}
						aria-invalid={passwordTouched && !passwordValid}
						class="pr-10"
					/>
					<button
						type="button"
						class="absolute top-1/2 right-2 -translate-y-1/2 text-muted-foreground transition-colors hover:text-foreground"
						onclick={() => (showPassword = !showPassword)}
						aria-label={showPassword ? 'Dölj lösenord' : 'Visa lösenord'}
					>
						{#if showPassword}
							<EyeOffIcon class="h-4 w-4" />
						{:else}
							<EyeIcon class="h-4 w-4" />
						{/if}
					</button>
				</div>
				{#if passwordTouched && !passwordValid}
					<p class="text-sm text-destructive">Lösenord krävs.</p>
				{/if}
			</div>

			<!-- Remember checkbox -->
			{#if allowPersist}
				<div class="flex items-center gap-2 pt-4 pb-4">
					<Checkbox id="persist" bind:checked={persist} />
					<Label for="persist" class="cursor-pointer font-normal">Kom ihåg på denna enhet</Label>
				</div>
			{/if}
		</CardContent>

		<CardFooter>
			<Button type="submit" disabled={!canSubmit} class="w-full">
				{#if loading}
					<Loader2Icon class="mr-2 h-4 w-4 animate-spin" />
					Verifierar…
				{:else}
					{submitLabel}
				{/if}
			</Button>
		</CardFooter>
	</form>
</Card>
