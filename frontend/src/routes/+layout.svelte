<script lang="ts">
	import './layout.css';
	import favicon from '$lib/assets/favicon.svg';
	import Navbar from '$lib/components/Navbar.svelte';
	import { createApiClient } from '$lib/api';
	import { currentUser } from '$lib/auth/currentUser.svelte';

	let { children } = $props();

	$effect(() => {
		const api = createApiClient({ cookieAuth: true });
		api.getMe()
			.then((user) => currentUser.set(user))
			.catch(() => {
				// not logged in — leave currentUser.user as null
			});
	});
</script>

<svelte:head>
	<link rel="icon" href={favicon} />
	<title>Golfkompis</title>
</svelte:head>

<Navbar />
{@render children()}
