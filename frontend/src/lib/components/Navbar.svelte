<script lang="ts">
	import { page } from '$app/state';
	import { Button } from '$lib/components/ui/button';
	import { createApiClient } from '$lib/api';
	import { currentUser } from '$lib/auth/currentUser.svelte';
	import { mingolfProfile } from '$lib/auth/mingolfProfile.svelte';

	let loginOpen = $state(false);

	async function handleAppLogout() {
		const api = createApiClient();
		try {
			await api.logout();
		} finally {
			currentUser.clear();
		}
	}

	async function handleMingolfLogout() {
		const api = createApiClient();
		try {
			const updated = await api.patchMyMingolf({ mingolf_username: null, mingolf_password: null });
			currentUser.set(updated);
			mingolfProfile.clear();
		} catch {
			// ignore errors — user can try again
		}
	}
</script>

<header class="sticky top-0 z-40 border-b bg-background">
	<div class="mx-auto flex h-14 max-w-5xl items-center gap-6 px-4">
		<!-- Brand -->
		<!-- eslint-disable-next-line svelte/no-navigation-without-resolve -->
		<a href="/" class="text-lg font-bold tracking-tight">Golfkompis</a>

		<!-- Nav links -->
		<!-- eslint-disable svelte/no-navigation-without-resolve -->
		<nav class="flex items-center gap-4 text-sm">
			<a
				href="/"
				class={page.url.pathname === '/'
					? 'font-medium text-foreground'
					: 'text-muted-foreground transition-colors hover:text-foreground'}
			>
				Hem
			</a>
			<a
				href="/profile"
				class={page.url.pathname === '/profile'
					? 'font-medium whitespace-nowrap text-foreground'
					: 'whitespace-nowrap text-muted-foreground transition-colors hover:text-foreground'}
			>
				Min sida
			</a>
			<a
				href="/book"
				class={page.url.pathname === '/book'
					? 'font-medium text-foreground'
					: 'text-muted-foreground transition-colors hover:text-foreground'}
			>
				Boka
			</a>
			<a
				href={currentUser.isLoggedIn ? '/profile/account' : '/login'}
				class={page.url.pathname.startsWith('/profile/account') ||
				(page.url.pathname as string) === '/login'
					? 'font-medium text-foreground'
					: 'text-muted-foreground transition-colors hover:text-foreground'}
			>
				Konto
			</a>
		</nav>
		<!-- eslint-enable svelte/no-navigation-without-resolve -->

		<div class="flex-1"></div>

		<!-- App auth area -->
		{#if currentUser.isLoggedIn}
			<span class="hidden text-sm text-muted-foreground sm:inline">
				{currentUser.user?.username ?? currentUser.user?.email}
			</span>
			<Button variant="ghost" size="sm" onclick={handleAppLogout}>Logga ut konto</Button>
		{:else}
			<!-- eslint-disable-next-line svelte/no-navigation-without-resolve -->
			<a href="/login">
				<Button variant="ghost" size="sm">Logga in konto</Button>
			</a>
		{/if}

		<!-- MinGolf auth area -->
		{#if mingolfProfile.profile}
			<span class="hidden text-sm text-muted-foreground sm:inline">
				{mingolfProfile.profile.firstName}
				{mingolfProfile.profile.lastName} · HCP {mingolfProfile.profile.hcp}
			</span>
			<Button variant="outline" size="sm" onclick={handleMingolfLogout}>MinGolf ut</Button>
		{/if}
	</div>
</header>
