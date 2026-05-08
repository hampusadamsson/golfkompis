<script lang="ts">
	import { page } from '$app/state';
	import { Button } from '$lib/components/ui/button';
	import {
		Sheet,
		SheetContent,
		SheetTrigger,
		SheetClose
	} from '$lib/components/ui/sheet';
	import { createApiClient } from '$lib/api';
	import { currentUser } from '$lib/auth/currentUser.svelte';
	import { mingolfProfile } from '$lib/auth/mingolfProfile.svelte';
	import MenuIcon from '@lucide/svelte/icons/menu';

	type NavLink = { href: string; label: string; isActive: (p: string) => boolean };

	const navLinks: NavLink[] = [
		{ href: '/', label: 'Hem', isActive: (p) => p === '/' },
		{ href: '/profile', label: 'Min sida', isActive: (p) => p === '/profile' },
		{ href: '/book', label: 'Boka', isActive: (p) => p === '/book' }
	];

	function linkClass(active: boolean) {
		return active
			? 'font-medium text-foreground'
			: 'text-muted-foreground transition-colors hover:text-foreground';
	}

	let mobileOpen = $state(false);

	async function handleAppLogout() {
		const api = createApiClient();
		try {
			await api.logout();
		} finally {
			currentUser.clear();
			mingolfProfile.clear();
		}
	}
</script>

<!-- eslint-disable svelte/no-navigation-without-resolve -->
<header class="sticky top-0 z-40 border-b bg-background">
	<div class="mx-auto flex h-14 max-w-5xl items-center gap-6 px-4">
		<!-- Brand -->
		<a href="/" class="text-lg font-bold tracking-tight">Golfkompis</a>

		<!-- Desktop nav links + auth -->
		<nav class="hidden items-center gap-4 text-sm md:flex" aria-label="Huvudnavigation">
			{#each navLinks as link (link.href)}
				<a
					href={link.href}
					class={linkClass(link.isActive(page.url.pathname))}
					aria-current={link.isActive(page.url.pathname) ? 'page' : undefined}
				>
					{link.label}
				</a>
			{/each}
			{#if currentUser.isLoggedIn}
				<button class={linkClass(false)} onclick={handleAppLogout}>Logga ut</button>
			{:else}
				<a href="/login" class={linkClass(page.url.pathname === '/login')}>Logga in</a>
			{/if}
		</nav>

		<div class="flex-1"></div>

		{#if currentUser.isLoggedIn}
			<a
				href="/profile/account"
				class="hidden text-sm text-muted-foreground transition-colors hover:text-foreground md:inline"
			>
				{currentUser.user?.username ?? currentUser.user?.email}
			</a>
		{/if}

		<!-- Mobile hamburger -->
		<Sheet bind:open={mobileOpen}>
			<SheetTrigger>
				<Button
					variant="ghost"
					size="icon"
					aria-label="Öppna meny"
					class="md:hidden"
					onclick={() => (mobileOpen = true)}
				>
					<MenuIcon class="h-5 w-5" />
				</Button>
			</SheetTrigger>
			<SheetContent side="right" class="w-64 pt-10">
				<nav class="flex flex-col gap-1" aria-label="Mobilnavigation">
					{#each navLinks as link (link.href)}
						<SheetClose>
							<a
								href={link.href}
								onclick={() => (mobileOpen = false)}
								class="flex w-full rounded-md px-3 py-2 text-base font-medium {link.isActive(
									page.url.pathname
								)
									? 'bg-muted text-foreground'
									: 'text-muted-foreground hover:bg-muted hover:text-foreground'} transition-colors"
								aria-current={link.isActive(page.url.pathname) ? 'page' : undefined}
							>
								{link.label}
							</a>
						</SheetClose>
					{/each}
					<div class="my-1 border-t"></div>
					{#if currentUser.isLoggedIn}
						<SheetClose>
							<a
								href="/profile/account"
								onclick={() => (mobileOpen = false)}
								class="flex w-full rounded-md px-3 py-2 text-base font-medium {page.url.pathname.startsWith('/profile/account') ? 'bg-muted text-foreground' : 'text-muted-foreground hover:bg-muted hover:text-foreground'} transition-colors"
							>
								{currentUser.user?.username ?? currentUser.user?.email}
							</a>
						</SheetClose>
						<SheetClose>
							<button
								onclick={() => { mobileOpen = false; handleAppLogout(); }}
								class="flex w-full rounded-md px-3 py-2 text-base font-medium text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
							>
								Logga ut
							</button>
						</SheetClose>
					{:else}
						<SheetClose>
							<a
								href="/login"
								onclick={() => (mobileOpen = false)}
								class="flex w-full rounded-md px-3 py-2 text-base font-medium text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
							>
								Logga in
							</a>
						</SheetClose>
					{/if}
				</nav>
			</SheetContent>
		</Sheet>
	</div>
</header>
<!-- eslint-enable svelte/no-navigation-without-resolve -->
