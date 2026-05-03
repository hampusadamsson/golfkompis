<script lang="ts">
	import { currentUser } from '$lib/auth/currentUser.svelte.js';
	import { Alert, AlertDescription } from '$lib/components/ui/alert';
	import Profile from '$lib/components/Profile.svelte';
	import UpcomingBookings from '$lib/components/UpcomingBookings.svelte';
	import History from '$lib/components/History.svelte';
	import Friends from '$lib/components/Friends.svelte';
</script>

<svelte:head><title>Min sida – Golfkompis</title></svelte:head>

{#if !currentUser.user}
	<div class="container mx-auto max-w-2xl px-4 py-8">
		<Alert>
			<AlertDescription>
				Du måste logga in för att se din sida.
				<!-- eslint-disable-next-line svelte/no-navigation-without-resolve -->
				<a href="/login" class="underline">Logga in</a>
			</AlertDescription>
		</Alert>
	</div>
{:else if !currentUser.user.mingolf_username}
	<div class="container mx-auto max-w-2xl px-4 py-8">
		<Alert>
			<AlertDescription>
				Koppla ditt MinGolf-konto för att se bokningar och vänner.
				<!-- eslint-disable-next-line svelte/no-navigation-without-resolve -->
				<a href="/profile/account" class="underline">Koppla MinGolf</a>
			</AlertDescription>
		</Alert>
	</div>
{:else}
	<div class="container mx-auto max-w-2xl px-4 pt-6">
		<Profile />
	</div>
	<section class="mx-auto w-full max-w-2xl space-y-10 px-4 py-12">
		<UpcomingBookings />
		<History />
		<Friends />
	</section>
{/if}
