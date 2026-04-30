<script lang="ts">
	import BookingFind from '$lib/components/BookingFind.svelte';
	import CredentialsForm from '$lib/components/CredentialsForm.svelte';
	import { credentials } from '$lib/auth/credentials.svelte';
</script>

<svelte:head><title>Boka – Golfkompis</title></svelte:head>

{#if !credentials.profile}
	<section class="flex flex-col items-center px-4 py-16">
		<CredentialsForm />
	</section>
{:else}
	<section class="mx-auto w-full max-w-2xl px-4 py-12">
		<BookingFind />
	</section>
{/if}
