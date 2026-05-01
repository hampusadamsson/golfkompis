<script lang="ts">
	import './layout.css';
	import favicon from '$lib/assets/favicon.svg';
	import Navbar from '$lib/components/Navbar.svelte';
	import { createApiClient } from '$lib/api';
	import { currentUser } from '$lib/auth/currentUser.svelte';
	import { mingolfProfile } from '$lib/auth/mingolfProfile.svelte.js';

	let { children } = $props();

	$effect(() => {
		const api = createApiClient({ cookieAuth: true });
		api
			.getMe()
			.then((user) => {
				currentUser.set(user);
				if (user.mingolf_username) {
					mingolfProfile.load(api);
				}
			})
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
