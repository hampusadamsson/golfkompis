<script lang="ts">
	import './layout.css';
	import favicon from '$lib/assets/favicon.svg';
	import Navbar from '$lib/components/Navbar.svelte';
	import Footer from '$lib/components/Footer.svelte';
	import { createApiClient, setGlobalOnUnauthorized } from '$lib/api';
	import { currentUser } from '$lib/auth/currentUser.svelte';
	import { mingolfProfile } from '$lib/auth/mingolfProfile.svelte.js';
	import { goto } from '$app/navigation';
	import { page } from '$app/state';

	let { children } = $props();

	// Routes accessible without being logged in — 401s here are expected.
	const PUBLIC_ROUTES = ['/login', '/register', '/forgot-password', '/reset-password', '/verify'];

	// Global 401 interceptor — clears auth state and redirects to /login,
	// but is a no-op on public routes where unauthenticated access is expected.
	setGlobalOnUnauthorized(() => {
		const path = page.url.pathname;
		if (PUBLIC_ROUTES.some((p) => path === p || path.startsWith(`${p}/`))) return;
		currentUser.clear();
		mingolfProfile.clear();
		goto('/login');
	});

	$effect(() => {
		// Bootstrap probe — a 401 here just means "not logged in", not an error.
		// Use a per-call no-op to prevent the global handler from bouncing the user.
		const api = createApiClient({ onUnauthorized: () => {} });
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

<a
	href="#main"
	class="sr-only focus:not-sr-only focus:absolute focus:left-4 focus:top-4 focus:z-50 focus:rounded-md focus:bg-background focus:px-4 focus:py-2 focus:text-sm focus:font-medium focus:shadow-md"
>
	Hoppa till innehåll
</a>

<Navbar />

<main id="main" tabindex="-1">
	{@render children()}
</main>

<Footer />
