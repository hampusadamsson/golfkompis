<script lang="ts">
	import { Alert, AlertDescription } from '$lib/components/ui/alert';
	import { Badge } from '$lib/components/ui/badge';
	import TriangleAlertIcon from '@lucide/svelte/icons/triangle-alert';

	import { createApiClient, getErrorMessage } from '$lib/api';
	import type { FriendOverview } from '$lib/api';
	import { credentials } from '$lib/auth/credentials.svelte';

	interface Props {
		apiBaseUrl?: string;
	}

	let { apiBaseUrl = '' }: Props = $props();

	let loading = $state(false);
	let errorMessage = $state<string | null>(null);
	let data = $state<FriendOverview | null>(null);

	$effect(() => {
		const creds = credentials.value;
		if (!creds) return;

		const controller = new AbortController();
		loading = true;
		errorMessage = null;

		const api = createApiClient({ baseUrl: apiBaseUrl, credentials: creds });
		api
			.getFriends({ signal: controller.signal })
			.then((res) => {
				data = res;
			})
			.catch((err) => {
			if ((err as { name?: string }).name === 'AbortError') return;
			errorMessage = getErrorMessage(err);
		})
			.finally(() => {
				loading = false;
			});

		return () => controller.abort();
	});

	function sortByFirstName(friends: FriendOverview['friends']) {
		return [...friends].sort((a, b) => a.firstName.localeCompare(b.firstName));
	}
</script>

<section class="border rounded-xl p-4">
	<div class="mb-4 flex items-center justify-between">
		<h2 class="text-xl font-semibold">Vänner</h2>
		{#if !loading && !errorMessage && data}
			<Badge variant="secondary" class="text-xs">{data.friends.length} vänner</Badge>
		{/if}
	</div>

	{#if loading}
		<ul class="divide-y">
			{#each [0, 1, 2, 3] as n (n)}
				<li class="flex items-center gap-3 py-3">
					<div class="bg-muted h-4 flex-1 animate-pulse rounded"></div>
					<div class="bg-muted h-5 w-12 animate-pulse rounded-full"></div>
				</li>
			{/each}
		</ul>
	{:else if errorMessage}
		<Alert variant="destructive">
			<TriangleAlertIcon class="h-4 w-4" />
			<AlertDescription>{errorMessage}</AlertDescription>
		</Alert>
	{:else if data}
		{@const sorted = sortByFirstName(data.friends)}
		{#if sorted.length === 0}
			<p class="text-muted-foreground text-sm">Inga vänner ännu.</p>
		{:else}
			<ul class="divide-y">
				{#each sorted as friend (friend.personId)}
					<li class="flex items-center gap-3 py-3">
						<span class="min-w-0 flex-1">
							<span class="text-sm font-medium">{friend.firstName} {friend.lastName}</span>
							{#if friend.homeClub}
								<span class="text-muted-foreground ml-2 text-xs">{friend.homeClub}</span>
							{/if}
						</span>
						<Badge variant="outline" class="shrink-0 text-xs">
							HCP {friend.hcp || '—'}
						</Badge>
					</li>
				{/each}
			</ul>
		{/if}
	{/if}
</section>
