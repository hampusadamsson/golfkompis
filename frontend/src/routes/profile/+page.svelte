<script lang="ts">
	import CredentialsForm from '$lib/components/CredentialsForm.svelte';
	import UpcomingBookings from '$lib/components/UpcomingBookings.svelte';
	import History from '$lib/components/History.svelte';
	import Friends from '$lib/components/Friends.svelte';
	import Profile from '$lib/components/Profile.svelte';
	import { credentials } from '$lib/auth/credentials.svelte';
</script>

<svelte:head><title>Min sida – Golfkompis</title></svelte:head>

{#if !credentials.profile}
	<section class="flex flex-col items-center px-4 py-16">
		<CredentialsForm />
	</section>
{:else}
	<section class="mx-auto w-full max-w-2xl space-y-10 px-4 py-12">
		<Profile />
		<UpcomingBookings />
		<History />
		<Friends />
	</section>
{/if}
