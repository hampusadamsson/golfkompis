<script lang="ts">
	import { page } from '$app/state';
	import { Button } from '$lib/components/ui/button';
	import {
		Dialog,
		DialogContent,
		DialogHeader,
		DialogTitle,
		DialogTrigger
	} from '$lib/components/ui/dialog';
	import CredentialsForm from './CredentialsForm.svelte';
	import { credentials } from '$lib/auth/credentials.svelte';

	let loginOpen = $state(false);

	function handleSignIn() {
		loginOpen = false;
	}
</script>

<header class="border-b bg-background sticky top-0 z-40">
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
					? 'text-foreground font-medium'
					: 'text-muted-foreground hover:text-foreground transition-colors'}
			>
				Hem
			</a>
			<a
				href="/profile"
				class={page.url.pathname === '/profile'
					? 'text-foreground font-medium'
					: 'text-muted-foreground hover:text-foreground transition-colors'}
			>
				Min sida
			</a>
			<a
				href="/book"
				class={page.url.pathname === '/book'
					? 'text-foreground font-medium'
					: 'text-muted-foreground hover:text-foreground transition-colors'}
			>
				Boka
			</a>
		</nav>
		<!-- eslint-enable svelte/no-navigation-without-resolve -->

		<div class="flex-1"></div>

		<!-- Auth area -->
		{#if credentials.profile}
			<span class="text-muted-foreground hidden text-sm sm:inline">
				{credentials.profile.firstName}
				{credentials.profile.lastName} · HCP {credentials.profile.hcp}
			</span>
			<Button variant="outline" size="sm" onclick={() => credentials.clear()}>Logga ut</Button>
		{:else}
			<Dialog bind:open={loginOpen}>
				<DialogTrigger>
					{#snippet child({ props })}
						<Button size="sm" {...props}>Logga in</Button>
					{/snippet}
				</DialogTrigger>
				<DialogContent class="sm:max-w-md">
					<DialogHeader>
						<DialogTitle>Logga in</DialogTitle>
					</DialogHeader>
					<CredentialsForm onSubmit={handleSignIn} />
				</DialogContent>
			</Dialog>
		{/if}
	</div>
</header>
