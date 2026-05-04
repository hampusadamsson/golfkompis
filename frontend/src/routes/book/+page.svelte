<script lang="ts">
	import { currentUser } from '$lib/auth/currentUser.svelte.js';
	import { Alert, AlertDescription } from '$lib/components/ui/alert';
	import BookingFind from '$lib/components/BookingFind.svelte';
	import QueueList from '$lib/components/QueueList.svelte';

	let queueList: QueueList | undefined = $state();

	function handleEnqueued() {
		queueList?.refresh();
	}
</script>

<svelte:head><title>Boka – Golfkompis</title></svelte:head>

{#if !currentUser.user}
	<div class="container mx-auto max-w-2xl px-4 py-8">
		<Alert>
			<AlertDescription>
				Du måste logga in för att boka en starttid.
				<!-- eslint-disable-next-line svelte/no-navigation-without-restore -->
				<a href="/login" class="underline">Logga in</a>
			</AlertDescription>
		</Alert>
	</div>
{:else if !currentUser.user.mingolf_username}
	<div class="container mx-auto max-w-2xl px-4 py-8">
		<Alert>
			<AlertDescription>
				Koppla ditt MinGolf-konto för att boka starttider.
				<!-- eslint-disable-next-line svelte/no-navigation-without-restore -->
				<a href="/profile/account" class="underline">Koppla MinGolf</a>
			</AlertDescription>
		</Alert>
	</div>
{:else}
	<section class="mx-auto w-full max-w-2xl space-y-6 px-4 py-12">
		<BookingFind onEnqueued={handleEnqueued} />
		<QueueList bind:this={queueList} />
	</section>
{/if}
