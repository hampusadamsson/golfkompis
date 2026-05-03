<script lang="ts">
	import './layout.css';
	import favicon from '$lib/assets/favicon.svg';
	import Navbar from '$lib/components/Navbar.svelte';
	import { createApiClient, setGlobalOnUnauthorized } from '$lib/api';
	import { currentUser } from '$lib/auth/currentUser.svelte';
	import { mingolfProfile } from '$lib/auth/mingolfProfile.svelte.js';
	import { goto } from '$app/navigation';

	let { children } = $props();

	// Register global 401 interceptor — clears auth state and redirects to /login
	setGlobalOnUnauthorized(() => {
		currentUser.clear();
		mingolfProfile.clear();
		goto('/login');
	});

	$effect(() => {
		const api = createApiClient();
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
